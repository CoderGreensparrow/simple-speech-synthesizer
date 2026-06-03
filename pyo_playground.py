from pyo import *

"""
# Common cutoff frequency control
freq = Sig(1000)
freq.ctrl([SLMap(50, 5000, "lin", "value", 1000)], title="Cutoff Frequency")

# Common filter's Q control
q = Sig(5)
q.ctrl([SLMap(0.7, 20, "log", "value", 5)], title="Filter's Q")

# Second-order bandpass filter
bp1 = Reson(n, freq, q=q)
# Cascade of second-order bandpass filters
bp2 = Resonx(n, freq, q=q, stages=4)

# Interpolates between input objects to produce a single output
sel = Selector([bp1, bp2]).out()
sel.ctrl(title="Filter selector (0=Reson, 1=Resonx)")
"""  # interesting Reson and Resonx and Selector stuff, also see Sig() for controlling variables with ctrl

# ====

"""# Six random frequencies.
freqs = [random.uniform(1000, 3000) for i in range(6)]

# Six different plucking speeds.
pluck = Metro([0.9, 0.8, 0.6, 0.4, 0.3, 0.2]).play()

# LFO applied to the decay of the resonator.
decay = Sine(0.1).range(0.01, 0.15)

# Six ComplexRes filters.
rezos = ComplexRes(pluck, freqs, decay, mul=5).out()

# Change chime frequencies every 7.2 seconds
def new():
    freqs = [random.uniform(1000, 3000) for i in range(6)]
    rezos.freq = freqs

pat = Pattern(new, 7.2).play()"""  # huh...

# ====

"""# duplex=1 to tell the Server we need both input and output sounds.
s = Server(duplex=1).boot()

# Length of the impulse response in samples.
TLEN = 512

# Conversion to seconds for NewTable objects.
DUR = sampsToSec(TLEN)

# Excitation signal for the filters.
sf = Noise(0.5)

# Signal from the mic to record the kernels.
inmic = Input()

# Four tables and recorders.
t1 = NewTable(length=DUR, chnls=1)
r1 = TableRec(inmic, table=t1, fadetime=0.001)

...

# Interpolation control between the tables.
pha = Sig(0)
pha.ctrl(title="Impulse responses morphing")

# Morphing between the four impulse responses.
res = NewTable(length=DUR, chnls=1)
morp = TableMorph(pha, res, [t1, t2, t3, t4])

# Circular convolution between the excitation and the morphed kernel.
a = Convolve(sf, table=res, size=res.getSize(), mul=0.1).mix(2).out()"""  # table recording?

# ==== MATRIXES

s = Server(duplex=0).boot()

# Length of grains in samples (length of a row in the matrix).
SIZE = 8192
# Number of successive grains kept in memory (number of rows in the matrix).
STAGES = 32
# Amount of granularity. Lower value will repeat first grains in memory more often.
RND_LEVEL = 8  # 1 -> STAGES
# Number of overlaps.
OLAPS = 4
# Percentage of grains that play.
GATE = 100

# Length of a grain in seconds.
period = SIZE / s.getSamplingRate()

# Envelope of the grains.
env = CosTable([(0, 0), (300, 1), (1000, 0.4), (8191, 0)])

# Creates the matrix.
matrix = NewMatrix(SIZE, STAGES)

# The source sound to record in the matrix.
src = SfPlayer("../snds/baseballmajeur_m.aif", speed=1, loop=True, mul=0.3)

# The matrix recorder.
m_rec = MatrixRecLoop(src, matrix)

# Triggers to start the grains.
metro = Metro(time=period / OLAPS, poly=OLAPS).play()

# Allows a percentage of the triggers to pass.
trig = Percent(metro, GATE)

# Generates a ramp from 0 to 1 to read a row in the matrix.
x = TrigLinseg(trig, [(0, 0), (period, 1)])
# Randomly chooses a row, between 0 and RND_LEVEL, in the matrix.
y = TrigRandInt(trig, max=RND_LEVEL, mul=1.0 / STAGES)
# Reads the amplitude envelope.
amp = TrigEnv(trig, table=env, dur=period)

# Reads a row, applies the envelope, and outputs the result.
out = MatrixPointer(matrix, x, y, amp).out()

s.gui(locals())