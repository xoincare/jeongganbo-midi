#!/usr/bin/env python3
"""
정간보(Jeongganbo) → MIDI 변환기 v1.0

12율명 기반 음높이 매핑 + 정간 기반 박자 체계
황종 기준음 선택 가능 (Eb4=63 전통, C4=60 현대)

참조: jeongganbo-editor/jgb_editor/pitch_name.py (한자 매핑)
"""

import mido
from mido import MidiFile, MidiTrack, Message

# 12율명 → 반음 오프셋 (황종=0 기준, 상행)
# 황(黃)=0, 대(大)=1, 태(太)=2, 협(夾)=3, 고(姑)=4, 중(仲)=5,
# 유(蕤)=6, 임(林)=7, 이(夷)=8, 남(南)=9, 무(無)=10, 응(應)=11
YUL_SEMITONES = {
    '황': 0,  '黃': 0,
    '대': 1,  '大': 1,
    '태': 2,  '太': 2,
    '협': 3,  '夾': 3,
    '고': 4,  '姑': 4,
    '중': 5,  '仲': 5,
    '유': 6,  '蕤': 6,
    '임': 7,  '林': 7,
    '이': 8,  '夷': 8,
    '남': 9,  '南': 9,
    '무': 10, '無': 10,
    '응': 11, '應': 11,
}

# 쉼표 기호
REST_SYMBOLS = {'-', '▽', '△', '休', 'rest', ''}


class JeongganboConverter:
    """정간보 시퀀스를 MIDI로 변환"""

    def __init__(self, hwang_pitch=63):
        """
        hwang_pitch: 황종(黃)의 MIDI 노트 번호
            63 = Eb4 (전통 궁중악 기준)
            60 = C4  (현대 교육용)
            58 = Bb3 (향악/민속악 기준)
        """
        self.hwang_pitch = hwang_pitch

    def yul_to_midi(self, yul_name, octave=0):
        """
        율명 → MIDI 노트 번호
        octave: 0=기본, +1=높은 옥타브, -1=낮은 옥타브
        """
        if yul_name in REST_SYMBOLS:
            return None

        semitone = YUL_SEMITONES.get(yul_name)
        if semitone is None:
            print(f"  ⚠️ 알 수 없는 율명: '{yul_name}' → 쉼표 처리")
            return None

        return self.hwang_pitch + semitone + (octave * 12)

    def sequence_to_midi(self, sequence, output_file, bpm=60, instrument=0):
        """
        sequence: [(율명, 정간수, 옥타브), ...]
            예: [('황', 1, 0), ('태', 1, 0), ('중', 2, 0)]
            정간수 = 박자 길이 (1정간=1박)
        bpm: 분당 박수 (전통악 보통 40~80)
        instrument: GM instrument (0=피아노, 25=기타, 73=피리류, 109=백파이프)
        """
        mid = MidiFile()
        track = MidiTrack()
        mid.tracks.append(track)

        # 트랙 이름
        track.append(mido.MetaMessage('track_name', name='Jeongganbo', time=0))

        # 템포
        tempo = mido.bpm2tempo(bpm)
        track.append(mido.MetaMessage('set_tempo', tempo=tempo, time=0))

        # 악기 설정
        track.append(Message('program_change', program=instrument, time=0))

        tpb = mid.ticks_per_beat  # 기본 480

        for yul, dur, octv in sequence:
            midi_note = self.yul_to_midi(yul, octv)
            ticks = int(dur * tpb)

            if midi_note is None:
                # 쉼표: 시간만 경과
                track.append(Message('note_off', note=0, velocity=0, time=ticks))
            else:
                track.append(Message('note_on', note=midi_note, velocity=64, time=0))
                track.append(Message('note_off', note=midi_note, velocity=64, time=ticks))

        # End of track
        track.append(mido.MetaMessage('end_of_track', time=0))

        mid.save(output_file)
        return output_file

    def parse_simple_notation(self, text):
        """
        간이 정간보 텍스트 → 시퀀스
        형식: "황 태 중 임" (공백 구분, 각 1정간)
              "황2 태 -1 중" (숫자=정간수, -=쉼표)
              "황+1" (+ 뒤 숫자=옥타브)
        """
        sequence = []
        tokens = text.strip().split()

        for token in tokens:
            octave = 0
            dur = 1

            # 옥타브 표시 분리
            if '+' in token and token[-1].isdigit():
                parts = token.rsplit('+', 1)
                token = parts[0]
                octave = int(parts[1])
            elif token.startswith('-') and len(token) > 1 and token[1:].isdigit():
                # "-1" = 1정간 쉼표
                dur = int(token[1:])
                sequence.append(('-', dur, 0))
                continue

            # 정간수 표시 분리
            if len(token) > 1 and token[-1].isdigit() and token[-2] not in '0123456789':
                dur = int(token[-1])
                token = token[:-1]

            sequence.append((token, dur, octave))

        return sequence


def demo():
    """데모: 여러 테스트 시퀀스 생성"""
    import os

    outdir = os.path.dirname(os.path.abspath(__file__))

    conv = JeongganboConverter(hwang_pitch=63)  # Eb4 전통 기준

    # 1) 기본 12율 스케일 (황→응, 1옥타브 상행)
    scale = [
        ('황', 1, 0), ('대', 1, 0), ('태', 1, 0), ('협', 1, 0),
        ('고', 1, 0), ('중', 1, 0), ('유', 1, 0), ('임', 1, 0),
        ('이', 1, 0), ('남', 1, 0), ('무', 1, 0), ('응', 1, 0),
        ('황', 2, 1),  # 높은 황종으로 마무리
    ]
    f1 = conv.sequence_to_midi(scale, os.path.join(outdir, "test_12yul_scale.mid"), bpm=72)
    print(f"✅ 12율 스케일: {f1}")

    # 2) 평조 (5음: 황태중임무) — 궁중악 기본 선율
    pyeongjo = [
        ('황', 2, 0), ('태', 1, 0), ('중', 1, 0),
        ('임', 2, 0), ('무', 1, 0),
        ('황', 1, 1), ('무', 1, 0), ('임', 2, 0),
        ('중', 1, 0), ('태', 1, 0), ('황', 4, 0),
    ]
    f2 = conv.sequence_to_midi(pyeongjo, os.path.join(outdir, "test_pyeongjo.mid"), bpm=60)
    print(f"✅ 평조 선율: {f2}")

    # 3) 계면조 (5음: 중임무황태+1) — 슬픈/서정적
    gyemyeonjo = [
        ('중', 2, 0), ('임', 1, 0), ('무', 1, 0),
        ('황', 2, 1), ('태', 1, 1),
        ('황', 1, 1), ('무', 1, 0), ('임', 2, 0),
        ('중', 4, 0),
    ]
    f3 = conv.sequence_to_midi(gyemyeonjo, os.path.join(outdir, "test_gyemyeonjo.mid"), bpm=52)
    print(f"✅ 계면조 선율: {f3}")

    # 4) 텍스트 파싱 테스트
    text_input = "황2 태 중 임2 무 황+1 무 임2 중 태 황4"
    seq = conv.parse_simple_notation(text_input)
    f4 = conv.sequence_to_midi(seq, os.path.join(outdir, "test_text_parse.mid"), bpm=60)
    print(f"✅ 텍스트 파싱: {f4}")
    print(f"   입력: '{text_input}'")
    print(f"   파싱 결과: {seq}")

    # 5) 한자 입력 테스트
    hanja_seq = [
        ('黃', 2, 0), ('太', 1, 0), ('仲', 1, 0),
        ('林', 2, 0), ('無', 1, 0), ('黃', 4, 1),
    ]
    f5 = conv.sequence_to_midi(hanja_seq, os.path.join(outdir, "test_hanja.mid"), bpm=60)
    print(f"✅ 한자 입력: {f5}")

    # 요약
    print(f"\n📊 생성된 MIDI 파일 5개:")
    print(f"   황종 기준: Eb4 (MIDI {conv.hwang_pitch})")
    for f in [f1, f2, f3, f4, f5]:
        size = os.path.getsize(f)
        mid = MidiFile(f)
        notes = sum(1 for t in mid.tracks for m in t if m.type == 'note_on')
        print(f"   {os.path.basename(f)}: {size}B, {notes} notes, {mid.length:.1f}s")


if __name__ == "__main__":
    demo()
