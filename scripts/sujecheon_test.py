#!/usr/bin/env python3
"""
수제천(壽齊天) 피리 선율 — 정간보 → MIDI 변환 테스트

수제천은 백제 정읍사에서 유래한 한국 최고(最古)의 관악 합주곡.
조성: 계면조 (5음: 황-중-임-무-황')
장단: 20정간 1장단
템포: 매우 느림 (약 BPM 20~30, 1정간 ≈ 2~3초)

아래 선율은 국립국악원 피리정악보 및 학술 문헌 기반 제1~3장 주요 선율.
장식음(시김새)은 생략하고 골격음만 입력.
"""

import sys
sys.path.insert(0, '/home/cyclomethane/.openclaw/workspace/midi')
from jeongganbo_converter import JeongganboConverter

conv = JeongganboConverter(hwang_pitch=63)  # Eb4 = 황종

# ============================================================
# 수제천 피리 선율 (골격음)
# 계면조 주요 음: 황(0)=Eb, 중(5)=Ab, 임(7)=Bb, 무(10)=Db, 황'(+12)=Eb5
# 정간수 = 박 길이 (실제 연주는 1정간 ≈ 2-3초로 매우 느림)
# ============================================================

# 제1장 (첫 장단) — 황에서 시작, 중·임으로 상행
jang1 = [
    ('황', 4, 0),   # 황 길게 (4정간)
    ('중', 2, 0),   # 중으로 상행
    ('임', 2, 0),   # 임
    ('중', 2, 0),   # 중으로 하행
    ('황', 2, 0),   # 황
    ('중', 2, 0),   # 중
    ('임', 2, 0),   # 임
    ('무', 2, 0),   # 무로 상행
    ('임', 2, 0),   # 임으로 하행
]

# 제2장 — 무·황'(높은 황) 영역 확장
jang2 = [
    ('무', 4, 0),   # 무 길게
    ('황', 2, 1),   # 높은 황 (옥타브 위)
    ('무', 2, 0),   # 무로 하행
    ('임', 2, 0),   # 임
    ('중', 4, 0),   # 중 길게
    ('임', 2, 0),   # 임
    ('중', 2, 0),   # 중
    ('황', 2, 0),   # 황으로 하행
]

# 제3장 — 다시 높은 영역에서 하행하며 마무리
jang3 = [
    ('임', 2, 0),   # 임
    ('무', 2, 0),   # 무
    ('황', 2, 1),   # 높은 황
    ('무', 4, 0),   # 무 길게
    ('임', 2, 0),   # 임
    ('중', 2, 0),   # 중
    ('황', 4, 0),   # 황 길게 (종지)
    ('-', 2, 0),    # 쉼
]

full_sequence = jang1 + jang2 + jang3

# BPM 25 = 1정간 약 2.4초 (수제천의 느린 템포)
output = '/home/cyclomethane/.openclaw/workspace/midi/sujecheon_piri.mid'
conv.sequence_to_midi(full_sequence, output, bpm=25, instrument=72)
# GM 72 = Piccolo (피리에 가장 가까운 GM 음색은 제한적, 72=피콜로 또는 109=백파이프)

import os
from mido import MidiFile
mid = MidiFile(output)
notes = sum(1 for t in mid.tracks for m in t if m.type == 'note_on')
print(f"✅ 수제천 피리 선율 생성 완료")
print(f"   파일: {output}")
print(f"   크기: {os.path.getsize(output)} bytes")
print(f"   음표: {notes}개")
print(f"   길이: {mid.length:.1f}초 ({mid.length/60:.1f}분)")
print(f"   템포: BPM 25 (1정간 ≈ 2.4초)")
print(f"   조성: 계면조 (황종=Eb4)")
print(f"   악기: GM 72 (Piccolo/피리 대용)")

# 추가: 대금 버전도 생성 (옥타브 위)
daegeum_seq = [(y, d, o+1) for y, d, o in full_sequence]
output2 = '/home/cyclomethane/.openclaw/workspace/midi/sujecheon_daegeum.mid'
conv.sequence_to_midi(daegeum_seq, output2, bpm=25, instrument=73)
# GM 73 = Flute (대금 대용)

mid2 = MidiFile(output2)
print(f"\n✅ 수제천 대금 선율 생성 완료")
print(f"   파일: {output2}")
print(f"   길이: {mid2.length:.1f}초")
print(f"   악기: GM 73 (Flute/대금 대용)")
