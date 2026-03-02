#!/usr/bin/env python3
"""
정간보 OMR → 멀티트랙 MIDI 변환기

각 악기 파트를 별도 MIDI 트랙으로 분리.
파일명에서 악기 목록 추출, 빈 줄로 섹션(악기) 구분.
"""

import os
import sys
import re

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from omr_to_midi import parse_omr_score, parse_yul_token, BASE_YUL
from jeongganbo_converter import JeongganboConverter, YUL_SEMITONES

import mido
from mido import MidiFile, MidiTrack, Message

# 악기별 GM 매핑 + 옥타브 조정
INSTRUMENT_MAP = {
    'daegeum':  {'name': '대금',   'gm': 73,  'oct_shift': 1},   # Flute
    'piri':     {'name': '피리',   'gm': 68,  'oct_shift': 0},   # Oboe
    'haegeum':  {'name': '해금',   'gm': 110, 'oct_shift': 0},   # Fiddle → Bag pipe alt: 40 Violin
    'ajaeng':   {'name': '아쟁',   'gm': 42,  'oct_shift': -1},  # Cello
    'gayageum': {'name': '가야금', 'gm': 25,  'oct_shift': 0},   # Acoustic Guitar (Nylon)
    'geomungo': {'name': '거문고', 'gm': 24,  'oct_shift': -1},  # Acoustic Guitar (Steel)
}


def extract_instruments(filename):
    """파일명에서 악기 목록 추출"""
    # "수제천_daegeum_piri_haegeum_ajaeng.txt" → ['daegeum','piri','haegeum','ajaeng']
    base = filename.replace('.txt', '')
    # 첫 번째 악기 이름 시작 지점 찾기
    for inst in INSTRUMENT_MAP:
        idx = base.find('_' + inst)
        if idx != -1:
            inst_part = base[idx+1:]
            return inst_part.split('_')
    return []


def split_sections(text):
    """빈 줄로 섹션 분리"""
    sections = []
    current = []
    for line in text.split('\n'):
        if line.strip() == '':
            if current:
                sections.append('\n'.join(current))
                current = []
        else:
            current.append(line)
    if current:
        sections.append('\n'.join(current))
    return sections


def omr_to_multitrack_midi(omr_text, instruments, output_file, bpm=25, hwang_pitch=63):
    """OMR 텍스트 → 멀티트랙 MIDI"""
    conv = JeongganboConverter(hwang_pitch=hwang_pitch)
    sections = split_sections(omr_text)

    if len(sections) != len(instruments):
        print(f"  ⚠️ 섹션 수({len(sections)}) ≠ 악기 수({len(instruments)})")
        instruments = instruments[:len(sections)]
        while len(instruments) < len(sections):
            instruments.append(f'unknown_{len(instruments)}')

    mid = MidiFile()
    tempo = mido.bpm2tempo(bpm)
    tpb = mid.ticks_per_beat

    for i, (inst_key, section_text) in enumerate(zip(instruments, sections)):
        info = INSTRUMENT_MAP.get(inst_key, {'name': inst_key, 'gm': 0, 'oct_shift': 0})

        track = MidiTrack()
        mid.tracks.append(track)

        # 트랙 메타데이터
        track.append(mido.MetaMessage('track_name', name=inst_key, time=0))
        if i == 0:
            track.append(mido.MetaMessage('set_tempo', tempo=tempo, time=0))

        # 채널 할당 (ch9는 드럼이므로 스킵)
        ch = i if i < 9 else i + 1
        track.append(Message('program_change', channel=ch, program=info['gm'], time=0))

        # 섹션 파싱
        sequence = parse_omr_score(section_text)

        # 시퀀스를 MIDI 이벤트로
        for yul, dur, octv in sequence:
            midi_note = conv.yul_to_midi(yul, octv + info['oct_shift'])
            ticks = int(dur * tpb)

            if midi_note is None:
                track.append(Message('note_off', channel=ch, note=0, velocity=0, time=ticks))
            else:
                # 범위 클램프 (0-127)
                midi_note = max(0, min(127, midi_note))
                track.append(Message('note_on', channel=ch, note=midi_note, velocity=64, time=0))
                track.append(Message('note_off', channel=ch, note=midi_note, velocity=64, time=ticks))

        track.append(mido.MetaMessage('end_of_track', time=0))

    mid.save(output_file)
    return output_file


def convert_all_multitrack(scores_dir, output_dir, bpm=25):
    """모든 곡을 멀티트랙 MIDI로 변환"""
    os.makedirs(output_dir, exist_ok=True)
    results = []

    for fname in sorted(os.listdir(scores_dir)):
        if not fname.endswith('.txt'):
            continue

        instruments = extract_instruments(fname)
        if not instruments:
            print(f"  ⚠️ 악기 추출 실패: {fname}")
            continue

        with open(os.path.join(scores_dir, fname), 'r', encoding='utf-8') as f:
            text = f.read()

        basename = fname.replace('.txt', '_multitrack.mid')
        outpath = os.path.join(output_dir, basename)

        try:
            omr_to_multitrack_midi(text, instruments, outpath, bpm=bpm)
            mid = MidiFile(outpath)
            notes = sum(1 for t in mid.tracks for m in t if m.type == 'note_on')
            inst_names = [INSTRUMENT_MAP.get(i, {}).get('name', i) for i in instruments]
            print(f"  ✅ {fname.replace('.txt','')}: {len(instruments)}트랙 ({'/'.join(inst_names)}), {notes} notes")
            results.append((basename, len(instruments), notes))
        except Exception as e:
            print(f"  ❌ {fname}: {e}")

    return results


if __name__ == "__main__":
    scores_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)),
        "datasets/korean_jeongganbo/jeongganbo-omr/dataset/jeongganbo/omr_results_scores")
    output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)),
        "datasets/korean_jeongganbo/omr_midi_multitrack")

    print("🎵 정간보 OMR → 멀티트랙 MIDI 변환")
    print(f"   악기 매핑: {', '.join(f'{k}→{v['name']}(GM{v['gm']})' for k,v in INSTRUMENT_MAP.items())}")
    print()

    results = convert_all_multitrack(scores_dir, output_dir)

    print(f"\n📊 {len(results)}곡 멀티트랙 변환 완료")
    total_notes = sum(r[2] for r in results)
    print(f"   총 음표: {total_notes}")
