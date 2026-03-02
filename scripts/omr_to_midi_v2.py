#!/usr/bin/env python3
"""
정간보 OMR → 멀티트랙 MIDI 변환기 v2.0 (시김새 Pitch Bend 포함)

v1 대비 변경:
- 시김새 부호 → Pitch Bend 이벤트 생성
- 요성/퇴성/추성/전성 등 실제 국악 장식음 표현
"""

import os
import sys
import re

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from jeongganbo_converter import JeongganboConverter, YUL_SEMITONES
from sigimsae_pitchbend import get_sigimsae_events, extract_ornaments, SIGIMSAE_MAP

import mido
from mido import MidiFile, MidiTrack, Message

BASE_YUL = ['황', '대', '태', '협', '고', '중', '유', '임', '이', '남', '무', '응']

INSTRUMENT_MAP = {
    'daegeum':  {'name': 'daegeum',  'gm': 73,  'oct_shift': 1},
    'piri':     {'name': 'piri',     'gm': 68,  'oct_shift': 0},
    'haegeum':  {'name': 'haegeum',  'gm': 110, 'oct_shift': 0},
    'ajaeng':   {'name': 'ajaeng',   'gm': 42,  'oct_shift': -1},
    'gayageum': {'name': 'gayageum', 'gm': 25,  'oct_shift': 0},
    'geomungo': {'name': 'geomungo', 'gm': 24,  'oct_shift': -1},
}

# 시김새 전체 리스트 (파싱에서 제거할 때 사용)
ALL_ORNAMENTS = sorted(SIGIMSAE_MAP.keys(), key=len, reverse=True)
EXTRA_ORNAMENTS = ['떠이어표', '같은음표']  # pitch bend 없는 것들


def parse_yul_token_v2(token):
    """율명 + 시김새 분리 추출"""
    ornaments = extract_ornaments(token)

    # 장식음 제거하여 순수 율명 추출
    clean = token
    for orn in ALL_ORNAMENTS + EXTRA_ORNAMENTS:
        clean = clean.replace('_' + orn, '').replace(orn, '')
    clean = clean.strip('_').strip()

    if not clean or clean == '-' or clean == '쉼표' or clean in ('니', '노', '느나', '니나*'):
        return None, 0, ornaments

    # 옥타브 접두사
    octave = 0
    if clean.startswith('중청'):
        octave = 2
        clean = clean[2:]
    elif clean.startswith('청'):
        octave = 1
        clean = clean[1:]
    elif clean.startswith('배'):
        octave = -1
        clean = clean[1:]

    if clean in BASE_YUL:
        return clean, octave, ornaments

    return None, 0, ornaments


def parse_omr_section_v2(text):
    """OMR 섹션 텍스트 → (율명, 정간수, 옥타브, [시김새]) 시퀀스"""
    sequence = []
    lines = [l.strip() for l in text.strip().split('\n') if l.strip()]

    for line in lines:
        jeonggans = line.split('|')

        for jg in jeonggans:
            tokens = jg.strip().split()
            if not tokens:
                sequence.append(('-', 1, 0, []))
                continue

            notes_in_jg = []
            has_tie = False
            has_rest = False

            for t in tokens:
                parts = t.split(':')
                if len(parts) != 2:
                    continue

                name_part = parts[0]

                if name_part == '-' or name_part.startswith('-_'):
                    has_tie = True
                    # tie에도 시김새가 있을 수 있음
                    orns = extract_ornaments(name_part)
                    if orns and sequence:
                        sequence[-1] = (sequence[-1][0], sequence[-1][1], sequence[-1][2],
                                       sequence[-1][3] + orns)
                    continue
                if name_part == '쉼표':
                    has_rest = True
                    continue

                yul, octave, ornaments = parse_yul_token_v2(name_part)
                if yul:
                    notes_in_jg.append((yul, octave, ornaments))

            if notes_in_jg:
                dur = 1.0 / len(notes_in_jg)
                for yul, octv, orns in notes_in_jg:
                    sequence.append((yul, dur, octv, orns))
            elif has_tie:
                if sequence and sequence[-1][0] != '-':
                    last = sequence[-1]
                    sequence[-1] = (last[0], last[1] + 1, last[2], last[3])
                else:
                    sequence.append(('-', 1, 0, []))
            elif has_rest:
                sequence.append(('-', 1, 0, []))
            else:
                sequence.append(('-', 1, 0, []))

    return sequence


def split_sections(text):
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


def extract_instruments(filename):
    base = filename.replace('.txt', '')
    for inst in INSTRUMENT_MAP:
        idx = base.find('_' + inst)
        if idx != -1:
            return base[idx+1:].split('_')
    return []


def build_track_v2(sequence, conv, inst_info, channel, tpb):
    """시퀀스 → MIDI 트랙 (시김새 pitch bend 포함)"""
    track = MidiTrack()
    track.append(mido.MetaMessage('track_name', name=inst_info['name'], time=0))
    track.append(Message('program_change', channel=channel, program=inst_info['gm'], time=0))

    oct_shift = inst_info['oct_shift']
    sigimsae_count = 0

    for yul, dur, octv, ornaments in sequence:
        midi_note = conv.yul_to_midi(yul, octv + oct_shift)
        ticks = int(dur * tpb)

        if midi_note is None:
            track.append(Message('note_off', channel=channel, note=0, velocity=0, time=ticks))
            continue

        midi_note = max(0, min(127, midi_note))

        # 끊는표/특강표 → velocity 조정
        velocity = 64
        if '끊는표' in ornaments:
            velocity = 80
            ticks = int(ticks * 0.6)  # 스타카토
        if '특강표' in ornaments:
            velocity = 90

        # 시김새가 있는 음
        bend_ornaments = [o for o in ornaments if o in SIGIMSAE_MAP and SIGIMSAE_MAP[o] is not None]

        if bend_ornaments:
            # 첫 번째 시김새 적용 (복합 시김새는 첫 번째만)
            orn = bend_ornaments[0]
            bend_events, consumed = get_sigimsae_events(orn, tpb, ticks, channel)

            if bend_events:
                sigimsae_count += 1
                # Note On
                track.append(Message('note_on', channel=channel, note=midi_note,
                                    velocity=velocity, time=0))
                # Pitch Bend 이벤트들
                for evt in bend_events:
                    track.append(evt)
                # Note Off (남은 시간 = ticks - consumed)
                remaining = max(0, ticks - consumed)
                track.append(Message('note_off', channel=channel, note=midi_note,
                                    velocity=velocity, time=remaining))
                # Bend 리셋
                track.append(Message('pitchwheel', channel=channel, pitch=0, time=0))
                continue

        # 일반 음 (시김새 없음)
        track.append(Message('note_on', channel=channel, note=midi_note,
                            velocity=velocity, time=0))
        track.append(Message('note_off', channel=channel, note=midi_note,
                            velocity=velocity, time=ticks))

    track.append(mido.MetaMessage('end_of_track', time=0))
    return track, sigimsae_count


def convert_v2(scores_dir, output_dir, bpm=25):
    """모든 곡을 v2 (시김새 포함)로 변환"""
    os.makedirs(output_dir, exist_ok=True)
    conv = JeongganboConverter(hwang_pitch=63)
    results = []
    total_sigimsae = 0

    for fname in sorted(os.listdir(scores_dir)):
        if not fname.endswith('.txt'):
            continue

        instruments = extract_instruments(fname)
        if not instruments:
            continue

        with open(os.path.join(scores_dir, fname), 'r', encoding='utf-8') as f:
            text = f.read()

        sections = split_sections(text)
        if len(sections) != len(instruments):
            instruments = instruments[:len(sections)]

        mid = MidiFile()
        tempo = mido.bpm2tempo(bpm)
        tpb = mid.ticks_per_beat
        song_sigimsae = 0

        for i, (inst_key, section_text) in enumerate(zip(instruments, sections)):
            info = INSTRUMENT_MAP.get(inst_key, {'name': inst_key, 'gm': 0, 'oct_shift': 0})
            ch = i if i < 9 else i + 1

            sequence = parse_omr_section_v2(section_text)

            # 첫 트랙에 템포 설정
            track, sig_count = build_track_v2(sequence, conv, info, ch, tpb)
            if i == 0:
                track.insert(1, mido.MetaMessage('set_tempo', tempo=tempo, time=0))

            mid.tracks.append(track)
            song_sigimsae += sig_count

        basename = fname.replace('.txt', '_v2.mid')
        outpath = os.path.join(output_dir, basename)
        mid.save(outpath)

        notes = sum(1 for t in mid.tracks for m in t if m.type == 'note_on')
        bends = sum(1 for t in mid.tracks for m in t if m.type == 'pitchwheel')
        inst_names = '/'.join(instruments)
        print(f"  ✅ {fname.replace('.txt','')}: {notes} notes, {bends} bends, {song_sigimsae} 시김새")

        results.append((basename, notes, bends, song_sigimsae))
        total_sigimsae += song_sigimsae

    return results, total_sigimsae


if __name__ == "__main__":
    scores_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)),
        "../midi/datasets/korean_jeongganbo/jeongganbo-omr/dataset/jeongganbo/omr_results_scores")

    # workspace의 원본 데이터 경로도 체크
    if not os.path.exists(scores_dir):
        scores_dir = "/home/cyclomethane/.openclaw/workspace/midi/datasets/korean_jeongganbo/jeongganbo-omr/dataset/jeongganbo/omr_results_scores"

    output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'midi', 'v2_sigimsae')

    print("🎵 정간보 OMR → MIDI v2.0 (시김새 Pitch Bend)")
    print()

    results, total_sig = convert_v2(scores_dir, output_dir)

    total_notes = sum(r[1] for r in results)
    total_bends = sum(r[2] for r in results)
    print(f"\n📊 {len(results)}곡 변환 완료")
    print(f"   총 음표: {total_notes}")
    print(f"   총 Pitch Bend: {total_bends} 이벤트")
    print(f"   총 시김새 적용: {total_sig}개")
