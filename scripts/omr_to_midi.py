#!/usr/bin/env python3
"""
정간보 OMR 결과 → MIDI 변환기

jeongganbo-omr의 omr_results_scores 텍스트 형식을 파싱하여 MIDI로 변환.

OMR 인코딩 형식:
  - "|" = 정간(beat) 구분
  - "율명:위치" = 해당 위치에 율명
  - "-:위치" = 이전 음 지속 (tie)
  - "쉼표:위치" = 쉼표
  - "_" 뒤 = 시김새(장식) 부호: 흘림표, 미는표, 떠이어표, 느로니르 등
  - "청" 접두 = 1옥타브 위, "중청" = 2옥타브 위, "배" 접두 = 1옥타브 아래
  - 줄바꿈 = 장단(행) 구분
"""

import re
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from jeongganbo_converter import JeongganboConverter, YUL_SEMITONES

import mido
from mido import MidiFile, MidiTrack, Message

# 율명 매핑 (한글)
BASE_YUL = ['황', '대', '태', '협', '고', '중', '유', '임', '이', '남', '무', '응']


def parse_yul_token(token):
    """
    OMR 토큰에서 율명과 옥타브 추출
    예: '청황' → ('황', 1), '중청황' → ('황', 2), '배남' → ('남', -1), '황' → ('황', 0)
    장식 부호는 제거하고 골격음만 추출
    """
    # 장식 부호 제거 (시김새)
    ornaments = ['흘림표', '미는표', '떠이어표', '느로니르', '느니-르', '나니로', '나니나',
                 '노니로', '니나', '니레', '니레나', '노라', '노네', '루러표', '서침표',
                 '끊는표', '풀어내림표', '시루표', '늘임표', '특강표', '반길이표',
                 '나니르노니르', '너녜', '노리노', '같은음표', '요성표', '겹요성표']

    clean = token
    for orn in ornaments:
        clean = clean.replace('_' + orn, '').replace(orn, '')
    clean = clean.strip('_').strip()

    if not clean or clean == '-' or clean == '쉼표' or clean == '니' or clean == '노' or clean == '느나':
        return None, 0

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

    # 율명 확인
    if clean in BASE_YUL:
        return clean, octave

    # 복합 토큰 (예: "니나*" 등) → 무시
    return None, 0


def parse_omr_score(text, bpm=25):
    """
    OMR 결과 텍스트를 파싱하여 MIDI 시퀀스 생성

    각 "|" 구분이 1정간(1박)
    각 줄이 1장단
    """
    sequence = []
    lines = [l.strip() for l in text.strip().split('\n') if l.strip()]

    for line in lines:
        jeonggans = line.split('|')

        for jg in jeonggans:
            tokens = jg.strip().split()
            if not tokens:
                sequence.append(('-', 1, 0))
                continue

            # 이 정간에서 음표 추출
            notes_in_jg = []
            has_tie = False
            has_rest = False

            for t in tokens:
                # "율명:위치" 형식 파싱
                parts = t.split(':')
                if len(parts) != 2:
                    continue

                name_part = parts[0]
                # pos = parts[1]  # 위치 정보는 정간 내 세부 위치

                if name_part == '-':
                    has_tie = True
                    continue
                if name_part == '쉼표':
                    has_rest = True
                    continue

                yul, octave = parse_yul_token(name_part)
                if yul:
                    notes_in_jg.append((yul, octave))

            if notes_in_jg:
                # 정간 내 여러 음이 있으면 → 균등 분할
                dur = 1.0 / len(notes_in_jg)
                for yul, octv in notes_in_jg:
                    sequence.append((yul, dur, octv))
            elif has_tie:
                # 이전 음 지속
                if sequence and sequence[-1][0] != '-':
                    last = sequence[-1]
                    sequence[-1] = (last[0], last[1] + 1, last[2])
                else:
                    sequence.append(('-', 1, 0))
            elif has_rest:
                sequence.append(('-', 1, 0))
            else:
                # 빈 정간 = 이전 음 지속 또는 쉼
                sequence.append(('-', 1, 0))

    return sequence


def omr_to_midi(omr_text, output_file, bpm=25, instrument=72, hwang_pitch=63):
    """OMR 텍스트 → MIDI 파일"""
    conv = JeongganboConverter(hwang_pitch=hwang_pitch)
    sequence = parse_omr_score(omr_text, bpm)

    # 연속 쉼표 병합
    merged = []
    for yul, dur, octv in sequence:
        if yul == '-' and merged and merged[-1][0] == '-':
            merged[-1] = ('-', merged[-1][1] + dur, 0)
        else:
            merged.append((yul, dur, octv))

    conv.sequence_to_midi(merged, output_file, bpm=bpm, instrument=instrument)

    mid = MidiFile(output_file)
    notes = sum(1 for t in mid.tracks for m in t if m.type == 'note_on')
    return output_file, notes, mid.length


def convert_all_scores(scores_dir, output_dir, bpm=25):
    """모든 OMR 결과를 MIDI로 변환"""
    os.makedirs(output_dir, exist_ok=True)
    results = []

    for fname in sorted(os.listdir(scores_dir)):
        if not fname.endswith('.txt'):
            continue

        filepath = os.path.join(scores_dir, fname)
        with open(filepath, 'r', encoding='utf-8') as f:
            text = f.read()

        basename = fname.replace('.txt', '.mid')
        outpath = os.path.join(output_dir, basename)

        try:
            path, notes, length = omr_to_midi(text, outpath, bpm=bpm)
            results.append((basename, notes, length))
            print(f"  ✅ {basename}: {notes} notes, {length:.0f}s ({length/60:.1f}min)")
        except Exception as e:
            print(f"  ❌ {basename}: {e}")

    return results


if __name__ == "__main__":
    scores_dir = os.path.join(os.path.dirname(__file__),
        "datasets/korean_jeongganbo/jeongganbo-omr/dataset/jeongganbo/omr_results_scores")
    output_dir = os.path.join(os.path.dirname(__file__),
        "datasets/korean_jeongganbo/omr_midi")

    print(f"🎵 정간보 OMR → MIDI 일괄 변환")
    print(f"   입력: {scores_dir}")
    print(f"   출력: {output_dir}")
    print()

    results = convert_all_scores(scores_dir, output_dir)

    print(f"\n📊 결과: {len(results)}곡 변환 완료")
    total_notes = sum(r[1] for r in results)
    total_time = sum(r[2] for r in results)
    print(f"   총 음표: {total_notes}")
    print(f"   총 길이: {total_time/60:.0f}분 ({total_time/3600:.1f}시간)")
