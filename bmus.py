#!/usr/bin/env python

import struct
import binascii
import audiere
import time

FREQ_TABLE_OFFSET = 0x2be
FREQ_TABLE_SIZE = 0x60

SEQUENCE_PTR_TABLE_OFFSET = 0x37e

binary = ''
with open('BMUS.BIN') as f:
    binary = bytearray(f.read())

# build freqency table
frequencies = list()
for i in range(FREQ_TABLE_SIZE):
    offset = FREQ_TABLE_OFFSET + i * 2;
    frequencies.append(struct.unpack('<H', str(binary[offset:offset+2]))[0])

# get sequence data
sequence_offsets = list()
for i in range(struct.unpack('<H', str(binary[SEQUENCE_PTR_TABLE_OFFSET:SEQUENCE_PTR_TABLE_OFFSET+2]))[0]):
    offset = SEQUENCE_PTR_TABLE_OFFSET + 2 + i * 2
    sequence_offsets.append(struct.unpack('<H', str(binary[offset:offset+2]))[0])
sequences = list()
for i in range(len(sequence_offsets)):
    offset = sequence_offsets[i]
    next_offset = 0x100000
    if i < len(sequence_offsets)- 1: next_offset = sequence_offsets[i+1]
    sequences.append(binary[offset:next_offset])

class SoundMachine:
	def __init__(self, sequences, audiere_dev):
		self.seqs = sequences
		self.cur_seq = 0	# g_p_sequence
		self.dev = audiere_dev
		self.tone = None
		self.sound_stack = list()

		##### globals #####
		self.word_291 = 0
		self.byte_293 = 0
		self.byte_294 = 0
		self.byte_295 = 0
		self.byte_296 = 0
		self.byte_297 = 0
		self.is_active = 0
		self.word_291 = 0
		self.word_29c = 0
		self.word_2bc = 0
		self.word_29e = 0
		self.word_28f = 0
		self.action = 0
		###################

        def launch(self, action, sequence=0, bx=0):	# action = ah; sequence = al
		print 'launch(): action = %d' % action
		if action == 1:
			self.setup(sequence)
		elif action == 2:
			# set if
			self.playLoop()
			# clear cf
		elif action == 3:
			self.is_active = 0
			self.toneOff()
			# clear cf
		elif action == 5:
			if self.is_active != 0:
				# clear cf
				pass
			else:
				# set cf
				pass
		elif action == 7:
			self.word_291 = bx
			# clear cf
		else:
			# set cf
			pass

	def setup(self, seq):
		if seq < len(self.seqs):
			print 'setup(): sequence = %d/%d' % (seq + 1, len(self.seqs))
			self.cur_seq = self.seqs[seq]
			self.word_29c = self.seqs[seq]
			self.word_2bc = self.word_29e
			
			self.byte_293 = 0
			self.byte_294 = 0
			self.byte_295 = 0
			self.byte_296 = 0
			self.action = 0

			self.byte_297 = 100
			self.is_active = 0xff

			print 'sequence = ', binascii.hexlify(self.cur_seq)

			# clear cf

	def playLoop(self):
		print 'playLoop(): is_active = %d' % self.is_active
		if self.is_active != 0:
			print 'playLoop: action = %d' % self.action
			if self.action == 2:
				pass
				#todo call sub_22c etc.
			elif self.action == 8:
				if self.byte_298 != 0xff:
					self.byte_298 -= 1
					dx = 12
					ax = 0x34dc
					if self.word_28f != 0:
						# todo div thingy
						pass
					self.setFreqAndDo()
					self.toneOn()
					self.word_286 += self.byte_299
				else:
					self.action = 0
					self.__loop()
			else:
				if self.byte_294 != 0:
					self.byte_294 -= 1
				else:
					if self.byte_296 != 0:
						self.byte_296 -= 1
						self.byte_294 = self.byte_293
						time.sleep(0.05)
					else:
						self.action = 0
						self.__loop()

	def toneOff(self):
		if self.tone: self.tone.stop()

	def toneOn(self):
		if self.tone: self.tone.play()

	def setFreqAndDo(self, freq):
		if self.word_291 != 0:
			# todo - div stuff
			pass
		self.tone = self.dev.create_tone(freq)
		#todo weird jumping...???

	def __incSeq(self, num):
		self.cur_seq = self.cur_seq[num:]

	def __loop(self):
		c = self.cur_seq[0]
		self.__incSeq(1)
		
		print '__loop(): c = 0x%x' % c

		if c >= 0x20:
			tone_idx = (c - 0x20) / 2;
			freq = frequencies[tone_idx]
			self.setFreqAndDo(freq)
			self.toneOn()
			self.byte_294 = self.byte_293
			self.byte_296 = self.byte_295
		elif c == 0:
			self.byte_295 = self.cur_seq[0]
			self.byte_296 = self.cur_seq[0]
			self.__incSeq(1)
			self.__loop()
		elif c == 1:
			self.byte_297 = self.cur_seq[0]
			self.__incSeq(1)
			self.__loop()
		elif c == 2:
			self.action = 2
			self.byte_294 = self.byte_293
			self.byte_296 = self.byte_295
		elif c == 3:
			self.toneOff()
			self.byte_294 = self.byte_293
			self.byte_296 = self.byte_295
		elif c == 4:
			self.byte_293 = self.cur_seq[0]
			self.byte_294 = self.cur_seq[0]
			self.__incSeq(1)
			self.__loop()
		elif c == 5:
			self.cur_seq = self.sound_stack.pop()
			self.sound_stack.append(self.cur_seq)
			self.__loop()
		elif c == 6:
			seq_idx = self.cur_seq[0]
			self.__incSeq(1)
			if seq_idx < len(self.seqs):
				self.sound_stack.append(self.cur_seq)
				self.cur_seq = self.seqs[self_idx]
				self.__loop()
			else:
				self.__loop()
		elif c == 7:
			if len(self.sound_stack) == 0:
				self.toneOff()
				self.is_active = 0
			else:
				self.cur_seq = self.sound_stack.pop()
				self.__loop()
		elif c == 8:
			self.action = 8
			self.word_28f = self.cur_seq[:2]	
			self.__incSeq(2)
			self.byte_298 = self.cur_seq[0]
			self.__incSeq(1)
			self.byte_299 = self.cur_seq[0]
			self.__incSeq(1)
		else:
			print 'invalid sequence case (0x%x)!!' % c

SEQUENCE_NO = 5

sm = SoundMachine(sequences, audiere.open_device())
sm.launch(1, SEQUENCE_NO)

while True: sm.launch(2)
