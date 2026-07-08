// Pirates of the Caribbean-inspired background music generator
// 6/8 time, D minor, epic galloping strings, brass swells, driving percussion

class BGMEngine {
  constructor() {
    this.ctx = null;
    this.masterGain = null;
    this.isPlaying = false;
    this.bpm = 140; // dotted-quarter feel
    this.eighthDuration = 60 / this.bpm / 2;
    this.barDuration = this.eighthDuration * 6; // 6/8 time
    this.currentBar = 0;
    this.schedulerTimer = null;
    this.nextNoteTime = 0;
    this.scheduleAheadTime = 0.15;
    this.lookahead = 25;
  }

  init() {
    this.ctx = new (window.AudioContext || window.webkitAudioContext)();

    this.masterGain = this.ctx.createGain();
    this.masterGain.gain.value = 0.2;

    this.compressor = this.ctx.createDynamicsCompressor();
    this.compressor.threshold.value = -18;
    this.compressor.knee.value = 8;
    this.compressor.ratio.value = 4;
    this.compressor.attack.value = 0.003;
    this.compressor.release.value = 0.15;

    this.reverb = this.createReverb();
    this.dryGain = this.ctx.createGain();
    this.dryGain.gain.value = 0.65;
    this.wetGain = this.ctx.createGain();
    this.wetGain.gain.value = 0.35;

    this.masterGain.connect(this.dryGain);
    this.masterGain.connect(this.reverb);
    this.reverb.connect(this.wetGain);
    this.dryGain.connect(this.compressor);
    this.wetGain.connect(this.compressor);
    this.compressor.connect(this.ctx.destination);
  }

  createReverb() {
    const length = this.ctx.sampleRate * 2.5;
    const impulse = this.ctx.createBuffer(2, length, this.ctx.sampleRate);
    for (let ch = 0; ch < 2; ch++) {
      const data = impulse.getChannelData(ch);
      for (let i = 0; i < length; i++) {
        data[i] = (Math.random() * 2 - 1) * Math.pow(1 - i / length, 2.0);
      }
    }
    const convolver = this.ctx.createConvolver();
    convolver.buffer = impulse;
    return convolver;
  }

  start() {
    if (this.isPlaying) return;
    if (!this.ctx) this.init();
    if (this.ctx.state === 'suspended') this.ctx.resume();

    this.isPlaying = true;
    this.currentBar = 0;
    this.nextNoteTime = this.ctx.currentTime + 0.05;
    this.scheduler();
  }

  stop() {
    this.isPlaying = false;
    if (this.schedulerTimer) {
      clearTimeout(this.schedulerTimer);
      this.schedulerTimer = null;
    }
  }

  fadeOut(duration = 2) {
    if (!this.ctx || !this.masterGain) return;
    this.masterGain.gain.linearRampToValueAtTime(0, this.ctx.currentTime + duration);
    setTimeout(() => this.stop(), duration * 1000);
  }

  setVolume(v) {
    if (this.masterGain) {
      this.masterGain.gain.linearRampToValueAtTime(v, this.ctx.currentTime + 0.1);
    }
  }

  scheduler() {
    while (this.nextNoteTime < this.ctx.currentTime + this.scheduleAheadTime) {
      this.scheduleBar(this.nextNoteTime, this.currentBar);
      this.nextNoteTime += this.barDuration;
      this.currentBar++;
    }
    this.schedulerTimer = setTimeout(() => {
      if (this.isPlaying) this.scheduler();
    }, this.lookahead);
  }

  scheduleBar(time, bar) {
    const section = Math.floor(bar / 8) % 4;
    const barInSection = bar % 8;

    // Galloping rhythm (always)
    this.playGallop(time, section);

    // Melodic string line
    this.playMelody(time, bar, section);

    // Low strings/cello ostinato
    this.playCello(time, section);

    // Percussion - epic drums
    this.playPercussion(time, barInSection);

    // Brass swells every 4 bars
    if (barInSection === 0 || barInSection === 4) {
      this.playBrassSwell(time, section, barInSection);
    }

    // Soaring high strings on climax bars
    if (barInSection >= 6) {
      this.playHighStrings(time, section);
    }
  }

  // The iconic galloping pattern: short-short-long in 6/8
  playGallop(time, section) {
    const roots = [146.83, 146.83, 174.61, 130.81]; // D3, D3, F3, C3
    const fifth = [220, 220, 261.63, 196]; // A3, A3, C4, G3
    const root = roots[section];
    const fth = fifth[section];

    // Pattern: eighth-eighth-quarter, eighth-eighth-quarter (gallop feel)
    const pattern = [
      { time: 0, freq: root, dur: 0.8 },
      { time: 1, freq: root, dur: 0.8 },
      { time: 2, freq: fth, dur: 1.8 },
      { time: 3, freq: root, dur: 0.8 },
      { time: 4, freq: root, dur: 0.8 },
      { time: 5, freq: fth, dur: 0.8 },
    ];

    pattern.forEach(note => {
      const noteTime = time + note.time * this.eighthDuration;
      const duration = note.dur * this.eighthDuration;
      this.playStringNote(noteTime, note.freq, duration, 0.12, 'sawtooth');
    });
  }

  // Epic melody line inspired by "He's a Pirate" contour
  playMelody(time, bar, section) {
    // D minor melodic phrases
    const phrases = [
      // Phrase A: Rising heroic
      [[293.66, 2], [349.23, 1], [392, 2], [440, 1]],           // D4 F4 G4 A4
      [[440, 2], [392, 1], [349.23, 2], [293.66, 1]],           // A4 G4 F4 D4
      // Phrase B: Climbing tension
      [[293.66, 1], [329.63, 1], [349.23, 1], [392, 1], [440, 2]], // D4 E4 F4 G4 A4
      [[523.25, 2], [493.88, 1], [440, 2], [392, 1]],           // C5 B4 A4 G4
      // Phrase C: Triumphant
      [[587.33, 3], [523.25, 1], [440, 2]],                     // D5 C5 A4
      [[523.25, 2], [493.88, 1], [440, 3]],                     // C5 B4 A4
      // Phrase D: Resolution
      [[392, 2], [349.23, 1], [293.66, 3]],                     // G4 F4 D4
      [[349.23, 2], [329.63, 1], [293.66, 3]],                  // F4 E4 D4
    ];

    const phraseIndex = bar % phrases.length;
    const phrase = phrases[phraseIndex];

    let offset = 0;
    phrase.forEach(([freq, eighths]) => {
      const noteTime = time + offset * this.eighthDuration;
      const duration = eighths * this.eighthDuration * 0.9;
      this.playStringNote(noteTime, freq, duration, 0.09, 'sawtooth');
      offset += eighths;
    });
  }

  // Low cello driving rhythm
  playCello(time, section) {
    const bassNotes = [73.42, 73.42, 87.31, 65.41]; // D2, D2, F2, C2
    const freq = bassNotes[section];

    // Driving low-end: emphasize beats 1 and 4 (the two main beats in 6/8)
    const pattern = [
      { time: 0, vel: 1.0 },
      { time: 3, vel: 0.85 },
    ];

    pattern.forEach(beat => {
      const noteTime = time + beat.time * this.eighthDuration;
      this.plasCelloNote(noteTime, freq, this.eighthDuration * 2.5, beat.vel);
    });
  }

  plasCelloNote(time, freq, duration, velocity) {
    const osc1 = this.ctx.createOscillator();
    const osc2 = this.ctx.createOscillator();
    const gain = this.ctx.createGain();
    const filter = this.ctx.createBiquadFilter();

    osc1.type = 'sawtooth';
    osc1.frequency.setValueAtTime(freq, time);
    osc2.type = 'sawtooth';
    osc2.frequency.setValueAtTime(freq * 1.003, time);

    filter.type = 'lowpass';
    filter.frequency.setValueAtTime(600, time);
    filter.Q.value = 1;

    const vol = velocity * 0.2;
    gain.gain.setValueAtTime(0, time);
    gain.gain.linearRampToValueAtTime(vol, time + 0.02);
    gain.gain.setValueAtTime(vol * 0.8, time + duration * 0.6);
    gain.gain.linearRampToValueAtTime(0, time + duration);

    osc1.connect(filter);
    osc2.connect(filter);
    filter.connect(gain);
    gain.connect(this.masterGain);

    osc1.start(time);
    osc2.start(time);
    osc1.stop(time + duration + 0.01);
    osc2.stop(time + duration + 0.01);
  }

  playStringNote(time, freq, duration, volume, type) {
    const osc1 = this.ctx.createOscillator();
    const osc2 = this.ctx.createOscillator();
    const gain = this.ctx.createGain();
    const filter = this.ctx.createBiquadFilter();

    osc1.type = type || 'sawtooth';
    osc1.frequency.setValueAtTime(freq, time);
    osc2.type = type || 'sawtooth';
    osc2.frequency.setValueAtTime(freq * 1.004, time); // Detune for ensemble

    filter.type = 'lowpass';
    filter.frequency.setValueAtTime(2500, time);
    filter.frequency.linearRampToValueAtTime(1500, time + duration);
    filter.Q.value = 0.7;

    gain.gain.setValueAtTime(0, time);
    gain.gain.linearRampToValueAtTime(volume, time + 0.015);
    gain.gain.setValueAtTime(volume * 0.7, time + duration * 0.7);
    gain.gain.linearRampToValueAtTime(0, time + duration);

    osc1.connect(filter);
    osc2.connect(filter);
    filter.connect(gain);
    gain.connect(this.masterGain);

    osc1.start(time);
    osc2.start(time);
    osc1.stop(time + duration + 0.02);
    osc2.stop(time + duration + 0.02);
  }

  playPercussion(time, barInSection) {
    // Big epic drums: toms and kick on the main beats, snare accent
    // 6/8 feel: main pulses on 1 and 4

    // Low war drum on beat 1
    this.playWarDrum(time, 0.6);

    // Secondary hit on beat 4
    this.playWarDrum(time + 3 * this.eighthDuration, 0.4);

    // Snare/clap accent on last eighth for drive
    if (barInSection % 2 === 1) {
      this.playSnare(time + 5 * this.eighthDuration, 0.25);
    }

    // Cymbal roll on climax bars
    if (barInSection === 7) {
      for (let i = 0; i < 6; i++) {
        this.playCymbal(time + i * this.eighthDuration, 0.04 + i * 0.02);
      }
    }
  }

  playWarDrum(time, velocity) {
    const osc = this.ctx.createOscillator();
    const gain = this.ctx.createGain();

    osc.type = 'sine';
    osc.frequency.setValueAtTime(100, time);
    osc.frequency.exponentialRampToValueAtTime(45, time + 0.15);

    const vol = velocity * 0.35;
    gain.gain.setValueAtTime(vol, time);
    gain.gain.exponentialRampToValueAtTime(0.001, time + 0.4);

    osc.connect(gain);
    gain.connect(this.masterGain);

    osc.start(time);
    osc.stop(time + 0.45);

    // Body resonance
    const body = this.ctx.createOscillator();
    const bodyGain = this.ctx.createGain();
    body.type = 'sine';
    body.frequency.setValueAtTime(60, time);
    bodyGain.gain.setValueAtTime(vol * 0.5, time);
    bodyGain.gain.exponentialRampToValueAtTime(0.001, time + 0.6);
    body.connect(bodyGain);
    bodyGain.connect(this.masterGain);
    body.start(time);
    body.stop(time + 0.65);
  }

  playSnare(time, velocity) {
    const bufferSize = this.ctx.sampleRate * 0.1;
    const buffer = this.ctx.createBuffer(1, bufferSize, this.ctx.sampleRate);
    const data = buffer.getChannelData(0);
    for (let i = 0; i < bufferSize; i++) {
      data[i] = (Math.random() * 2 - 1) * Math.pow(1 - i / bufferSize, 4);
    }

    const source = this.ctx.createBufferSource();
    source.buffer = buffer;

    const filter = this.ctx.createBiquadFilter();
    filter.type = 'bandpass';
    filter.frequency.value = 3000;
    filter.Q.value = 1;

    const gain = this.ctx.createGain();
    gain.gain.setValueAtTime(velocity, time);
    gain.gain.linearRampToValueAtTime(0, time + 0.08);

    source.connect(filter);
    filter.connect(gain);
    gain.connect(this.masterGain);
    source.start(time);
  }

  playCymbal(time, velocity) {
    const bufferSize = this.ctx.sampleRate * 0.15;
    const buffer = this.ctx.createBuffer(1, bufferSize, this.ctx.sampleRate);
    const data = buffer.getChannelData(0);
    for (let i = 0; i < bufferSize; i++) {
      data[i] = (Math.random() * 2 - 1) * Math.pow(1 - i / bufferSize, 3);
    }

    const source = this.ctx.createBufferSource();
    source.buffer = buffer;

    const filter = this.ctx.createBiquadFilter();
    filter.type = 'highpass';
    filter.frequency.value = 6000;

    const gain = this.ctx.createGain();
    gain.gain.setValueAtTime(velocity, time);
    gain.gain.linearRampToValueAtTime(0, time + 0.12);

    source.connect(filter);
    filter.connect(gain);
    gain.connect(this.masterGain);
    source.start(time);
  }

  // Brass-like swells for grandeur
  playBrassSwell(time, section, barInSection) {
    const chords = {
      0: [146.83, 220, 293.66],      // Dm: D3 A3 D4
      1: [130.81, 196, 261.63],      // C:  C3 G3 C4
      2: [116.54, 174.61, 233.08],   // Bb: Bb2 F3 Bb3
      3: [110, 164.81, 220],         // A:  A2 E3 A3
    };

    const chord = chords[section];
    const swellDuration = this.barDuration * 2;

    chord.forEach((freq, i) => {
      const osc1 = this.ctx.createOscillator();
      const osc2 = this.ctx.createOscillator();
      const osc3 = this.ctx.createOscillator();
      const gain = this.ctx.createGain();
      const filter = this.ctx.createBiquadFilter();

      osc1.type = 'sawtooth';
      osc1.frequency.setValueAtTime(freq, time);
      osc2.type = 'sawtooth';
      osc2.frequency.setValueAtTime(freq * 1.002, time);
      osc3.type = 'square';
      osc3.frequency.setValueAtTime(freq * 0.999, time);

      filter.type = 'lowpass';
      filter.frequency.setValueAtTime(400, time);
      filter.frequency.linearRampToValueAtTime(1800, time + swellDuration * 0.6);
      filter.frequency.linearRampToValueAtTime(600, time + swellDuration);
      filter.Q.value = 1.5;

      const vol = barInSection === 0 ? 0.07 : 0.05;
      gain.gain.setValueAtTime(0, time);
      gain.gain.linearRampToValueAtTime(vol, time + swellDuration * 0.4);
      gain.gain.setValueAtTime(vol * 0.8, time + swellDuration * 0.7);
      gain.gain.linearRampToValueAtTime(0, time + swellDuration);

      osc1.connect(filter);
      osc2.connect(filter);
      osc3.connect(filter);
      filter.connect(gain);
      gain.connect(this.masterGain);

      osc1.start(time);
      osc2.start(time);
      osc3.start(time);
      osc1.stop(time + swellDuration + 0.1);
      osc2.stop(time + swellDuration + 0.1);
      osc3.stop(time + swellDuration + 0.1);
    });
  }

  // High soaring violin-like lines for climax
  playHighStrings(time, section) {
    const melodies = [
      [587.33, 659.25, 698.46, 783.99, 880], // D5 E5 F5 G5 A5
      [880, 783.99, 698.46, 659.25, 587.33], // A5 G5 F5 E5 D5
      [698.46, 783.99, 880, 1046.5, 880],    // F5 G5 A5 C6 A5
      [783.99, 698.46, 659.25, 587.33, 523.25], // G5 F5 E5 D5 C5
    ];

    const melody = melodies[section];
    const noteDur = this.eighthDuration * 1.1;

    melody.forEach((freq, i) => {
      if (i >= 6) return; // Only play what fits in the bar
      const noteTime = time + i * this.eighthDuration;

      const osc = this.ctx.createOscillator();
      const osc2 = this.ctx.createOscillator();
      const gain = this.ctx.createGain();
      const filter = this.ctx.createBiquadFilter();

      osc.type = 'sawtooth';
      osc.frequency.setValueAtTime(freq, noteTime);
      osc2.type = 'sawtooth';
      osc2.frequency.setValueAtTime(freq * 1.006, noteTime);

      filter.type = 'lowpass';
      filter.frequency.setValueAtTime(4000, noteTime);
      filter.Q.value = 0.5;

      gain.gain.setValueAtTime(0, noteTime);
      gain.gain.linearRampToValueAtTime(0.055, noteTime + 0.01);
      gain.gain.setValueAtTime(0.04, noteTime + noteDur * 0.6);
      gain.gain.linearRampToValueAtTime(0, noteTime + noteDur);

      osc.connect(filter);
      osc2.connect(filter);
      filter.connect(gain);
      gain.connect(this.masterGain);

      osc.start(noteTime);
      osc2.start(noteTime);
      osc.stop(noteTime + noteDur + 0.02);
      osc2.stop(noteTime + noteDur + 0.02);
    });
  }
}

window.BGMEngine = BGMEngine;
