# YAML util
# loader for musics

import re
import yaml
import numpy


# A loader for musics encoded in YAML
class MusicComposer:

    # Load a YAML file
    def __init__(self):
        self.musics = []

    # load a music from a YAML file
    def load_music(self, path):
        with open(path, 'r') as file:
            data = yaml.safe_load(file)

            # process each of the tracks
            tracks = data['tracks']
            for track in tracks:
                pass


# define notes in a track
class Note:

    # define a pattern for a note
    NOTE_PATTERN = re.compile("^[A-G](#|b)?[1-8]$")

    # constructor
    def __init__(self, config={}):
        self.silence  = config.get('silence' , False)
        self.duration = config.get('duration', 0.0  )
        self.halt     = config.get('halt'    , False)
        self.constant = config.get('constant', True )
        self.volume   = config.get('volume'  , 0    )
        self.loop     = config.get('loop'    , False)
        self.note     = config.get('note'    , None )
        self.counter  = config.get('counter' , 0    )

    # check that values are valid
    def __validate(self):
        if not (0 <= self.volume < 16):
            raise Exception(f'Invalid volume value: {self.volume}')
        if not (0 <= self.counter < 32):
            raise Exception(f'Invalid counter value: {self.counter}')
        if self.note is not None and not self.NOTE_PATTERN.match(self.note):
            raise Exception(f'Invalid note value: {self.note}')

    # serialize the note into a sequence of bytes
    def serialize(self, frequencies, tempo=60.0):
        return bytearray([0b10000000 | int(self.duration * tempo)])



# define a pulse note
class NotePulse(Note):

    # define a sweep for a pulse note
    class Sweep:

        # constructor
        def __init__(self, config={}):
            self.period = config.get('period', 0    )
            self.negate = config.get('negate', False)
            self.shift  = config.get('shift' , 0    )

        # check that values are valid
        def __validate(self):
            if not (0 <= self.period < 8):
                raise Exception(f'Invalid period value: {self.period}')
            if not (0 <= self.shift < 8):
                raise Exception(f'Invalid shift value: {self.shift}')

    # constructor
    def __init__(self, config={}):
        super().__init__(config)

        # read the duty cycle
        duty = config.get('duty', 0)
        if   duty == "12.5%": duty = 0
        elif duty == "25%"  : duty = 1
        elif duty == "50%"  : duty = 2
        elif duty == "75%"  : duty = 3
        self.duty = duty

        # read the sweep configuration
        sweep = config.get('sweep', None)
        self.sweep = None if sweep is None else NotePulse.Sweep(sweep)

    # check that values are valid
    def __validate(self):
        super().__validate()
        if not (0 <= self.duty < 4):
            raise Exception(f'Invalid duty value: {self.duty}')

    # serialize the note into a sequence of bytes
    def serialize(self, frequencies, tempo=60.0):
        duration = int(self.duration * tempo)
        if self.silence:
            return bytearray([0b10000000 | duration])
        else:
            # compose the control byte
            control = self.__compose_control()

            # compose the sweep byte
            if self.sweep is None:
                sweep = 0b0
            else:
                sweep = (0b10000000
                    | (self.sweep.period << 4)
                    | (0b1000 if self.sweep.negate else 0b0)
                    | self.sweep.shift)

            # compose the low and high bytes
            high, low = self.__compose_frequency(frequencies)
            return bytearray([duration, control, sweep, low, high])

    # compose control byte for pulse and noise
    def __compose_control(self):
        return ((self.duty << 6) 
            | (0b00100000 if self.halt     else 0b0) 
            | (0b00010000 if self.constant else 0b0) 
            | self.volume)

    # compose the low and high bytes
    def __compose_frequency(self, frequencies):
        note = frequencies.get_note(self.note)
        return (self.counter << 3) | (note >> 8), 0xFF & note


# define a triangle note
class NoteTriangle(Note):

    # constructor
    def __init__(self, config={}):
        super().__init__(config)
        self.linear = config.get('linear', 0)

    # check that values are valid
    def __validate(self):
        super().__validate()
        if not (0 <= self.linear < 128):
            raise Exception(f'Invalid linear value: {self.linear}')

    # serialize the note into a sequence of bytes
    def serialize(self, frequencies, tempo=60.0):
        duration = int(self.duration * tempo)
        if self.silence:
            return bytearray([0b10000000 | duration])
        else:
            # compose the control byte
            control = (0b10000000 if self.halt else 0b0) | self.linear

            # compose the low and high bytes
            high, low = self.__compose_frequency(frequencies)
            return bytearray([duration, control, low, high])


# define a noise note
class NoteNoise(Note):

    # constructor
    def __init__(self, config={}):
        super().__init__(config)
        self.period = config.get('period', 0)

    # check that values are valid
    def __validate(self):
        super().__validate()
        if not (0 <= self.period < 16):
            raise Exception(f'Invalid period value: {self.period}')

    # serialize the note into a sequence of bytes
    def serialize(self, frequencies, tempo=60.0):
        duration = int(self.duration * tempo)
        if self.silence:
            return bytearray([0b10000000 | duration])
        else:
            # compose the control byte
            control = self.__compose_control()
            noise   = (0b10000000 if self.loop else 0b0) | self.period
            return bytearray([duration, control, noise])


# define a DMC note
class NoteDMC(Note):

    # constructor
    def __init__(self, config={}):
        super().__init__(config)
        self.trigger_irq = config.get('trigger_irq', False )
        self.frequency   = config.get('frequency'  , 0     )
        self.address     = config.get('address'    , 0x00)
        self.size        = config.get('size'       , 0x00)

    # check that values are valid
    def __validate(self):
        if not (0 <= self.frequency < 16):
            raise Exception(f'Invalid frequency value: {self.frequency}')
        if not (0 <= self.counter < 128):
            raise Exception(f'Invalid counter value: {self.counter}')
        if not (0 <= self.address < 0x100):
            raise Exception(f'Invalid address value: {self.address}')
        if not (0 <= self.size < 0x100):
            raise Exception(f'Invalid size value: {self.size}')

    # serialize the note into a sequence of bytes
    def serialize(self, frequencies, tempo=60.0):
        duration = int(self.duration * tempo)
        if self.silence:
            return bytearray([0b10000000 | duration])
        else:
            # compose the control byte
            control = (self.frequency
                | (0b10000000 if self.trigger_irq else 0b0)
                | (0b01000000 if self.loop        else 0b0))
            return bytearray([duration, control, self.address, self.size])


# table for mapping notes with frequencies
class FrequencyTable:

    # constructor
    def __init__(self, mode='NTSC'):
        if mode == 'NTSC':
            factor = 1790000.0
        elif mode == 'PAL':
            factor = 1662607.0
        else:
            raise Exception(f'Invalid mode: {mode}')

        size = (8, 12)
        self.frequencies = numpy.zeros(size, dtype=numpy.float64)
        self.table       = numpy.zeros(size, dtype=numpy.uint16)

        # compute the frequencies for each note of each octave
        octave_start = 55.0
        for x in range(size[0]):
            for y in range(size[1]):
                # compute the frequency
                frequency = octave_start * (2.0 ** (y / 12.0))
                self.frequencies[x, y] = frequency

                # compute the lookup table
                self.table[x, y] = round((factor / frequency * 16.0) - 1.0)
            octave_start *= 2.0

    # parse a note
    def __parse_note(note):
        # valid note format: C4, C#4, Cb4, C 4
        size = len(note)
        if 2 <= size <= 3:
            note   = note.encode()
            pitch  = (note[ 0] - 0x41) * 2 # 'A' = 0x41
            octave = (note[-1] - 0x31)     # '1' = 0x31

            # ajust the picth for notes without semitone
            if   pitch > 7: pitch -= 2 # note 'E'
            elif pitch > 2: pitch -= 1 # note 'B'

            # if a sharp or flat is specified
            if size == 3:
                shift = note[1]
                if   shift == 0x23: pitch += 1 # '#' = 0x23
                elif shift == 0x62: pitch -= 1 # 'b' = 0x62

            # return the parsed note
            return (pitch, octave)

        else:
            raise Exception("Invalid note: {}".format(note))


    # return the 16-bit encoding of the given note
    def get_note(self, note):
        if note is None:
            return 0
        else:
            (pitch, octave) = self.__parse_note(note)
            return self.table[octave, pitch]