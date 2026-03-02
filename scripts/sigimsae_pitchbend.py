#!/usr/bin/env python3
"""
시김새(장식음) → MIDI Pitch Bend 변환 모듈

시김새 종류와 Pitch Bend 매핑:
- 요성(搖聲): 음을 떨어줌 → 주기적 vibrato (sine wave bend)
- 퇴성/흘림표: 음 끝에서 아래로 → 하행 pitch bend curve
- 추성/미는표: 아래에서 밀어올림 → 상행 pitch bend curve
- 전성: 음을 돌려줌 → 위아래 왕복 bend
- 떠이어표: 이전 음에서 연결 → legato (짧은 gap 제거)
- 느로니르/나니로 등: 구음(口音) 장식 → 빠른 grace note 시퀀스
"""

import math
from mido import Message


# Pitch Bend 범위: -8192 ~ +8191 (14-bit)
# 기본 bend range = ±2 반음 (GM 표준)
# 8192 = +2 semitones, -8192 = -2 semitones
# 1 반음 = 4096

BEND_CENTER = 0       # 기본 위치 (no bend)
BEND_SEMITONE = 4096  # 1반음에 해당하는 bend 값
BEND_MAX = 8191
BEND_MIN = -8192


def generate_yoseong(ticks_per_beat, duration_ticks, channel=0, depth=0.5, cycles=3):
    """
    요성(搖聲) — 음을 떨어주는 vibrato
    depth: 반음 단위 (0.5 = 반음의 반)
    cycles: 진동 횟수
    """
    events = []
    steps = max(20, cycles * 10)  # 해상도
    step_time = duration_ticks // steps

    for i in range(steps):
        t = i / steps
        # Sine wave vibrato
        bend_val = int(depth * BEND_SEMITONE * math.sin(2 * math.pi * cycles * t))
        bend_val = max(BEND_MIN, min(BEND_MAX, bend_val))
        time = step_time if i > 0 else 0
        events.append(Message('pitchwheel', channel=channel, pitch=bend_val, time=time))

    # Reset bend
    events.append(Message('pitchwheel', channel=channel, pitch=0, time=step_time))
    return events, steps * step_time + step_time


def generate_toeseong(ticks_per_beat, duration_ticks, channel=0, depth=2.0):
    """
    퇴성/흘림표 — 음 끝에서 아래로 흘러내림
    음의 후반 1/3에서 시작, depth 반음만큼 하행
    """
    events = []
    # 전반 2/3은 평음
    stable_time = duration_ticks * 2 // 3
    bend_time = duration_ticks - stable_time
    steps = 15

    # 안정 구간
    events.append(Message('pitchwheel', channel=channel, pitch=0, time=stable_time))

    # 하행 bend
    step_time = bend_time // steps
    for i in range(steps):
        t = (i + 1) / steps
        bend_val = int(-depth * BEND_SEMITONE * t)
        bend_val = max(BEND_MIN, min(BEND_MAX, bend_val))
        events.append(Message('pitchwheel', channel=channel, pitch=bend_val, time=step_time))

    # Reset
    events.append(Message('pitchwheel', channel=channel, pitch=0, time=0))
    return events, duration_ticks


def generate_chuseong(ticks_per_beat, duration_ticks, channel=0, depth=2.0):
    """
    추성/미는표 — 아래에서 밀어올림
    음의 전반 1/3에서 상행, 나머지는 안정
    """
    events = []
    bend_time = duration_ticks // 3
    stable_time = duration_ticks - bend_time
    steps = 15

    # 시작: 아래에서
    start_bend = int(-depth * BEND_SEMITONE)
    events.append(Message('pitchwheel', channel=channel, pitch=max(BEND_MIN, start_bend), time=0))

    # 상행 bend
    step_time = bend_time // steps
    for i in range(steps):
        t = (i + 1) / steps
        bend_val = int(-depth * BEND_SEMITONE * (1 - t))
        bend_val = max(BEND_MIN, min(BEND_MAX, bend_val))
        events.append(Message('pitchwheel', channel=channel, pitch=bend_val, time=step_time))

    # 안정 구간
    events.append(Message('pitchwheel', channel=channel, pitch=0, time=stable_time))
    return events, duration_ticks


def generate_jeonseong(ticks_per_beat, duration_ticks, channel=0, depth=1.0):
    """
    전성 — 음을 위아래로 돌려줌 (turn)
    위→아래→원래 또는 아래→위→원래
    """
    events = []
    steps = 20
    step_time = duration_ticks // steps

    for i in range(steps):
        t = i / steps
        # 위→아래→원래 (한 사이클)
        if t < 0.25:
            bend_val = int(depth * BEND_SEMITONE * (t / 0.25))
        elif t < 0.5:
            bend_val = int(depth * BEND_SEMITONE * (1 - (t - 0.25) / 0.25))
        elif t < 0.75:
            bend_val = int(-depth * BEND_SEMITONE * ((t - 0.5) / 0.25))
        else:
            bend_val = int(-depth * BEND_SEMITONE * (1 - (t - 0.75) / 0.25))

        bend_val = max(BEND_MIN, min(BEND_MAX, bend_val))
        events.append(Message('pitchwheel', channel=channel, pitch=bend_val, time=step_time if i > 0 else 0))

    events.append(Message('pitchwheel', channel=channel, pitch=0, time=step_time))
    return events, steps * step_time + step_time


def generate_neulim(ticks_per_beat, duration_ticks, channel=0, depth=0.3, cycles=5):
    """
    늘임표 — 긴 음에 느린 vibrato
    요성보다 느리고 넓은 진동
    """
    return generate_yoseong(ticks_per_beat, duration_ticks, channel, depth=depth, cycles=cycles)


def generate_pulleonaelim(ticks_per_beat, duration_ticks, channel=0):
    """
    풀어내림표 — 위에서 부드럽게 내려옴
    시작 시 반음 위에서 시작하여 자연스럽게 원래 음으로
    """
    return generate_chuseong(ticks_per_beat, duration_ticks, channel, depth=1.0)


# 시김새 이름 → 생성 함수 매핑
SIGIMSAE_MAP = {
    # 요성류 (vibrato)
    '요성표': generate_yoseong,
    '겹요성표': lambda tpb, dur, ch=0: generate_yoseong(tpb, dur, ch, depth=0.8, cycles=5),

    # 퇴성류 (하행 bend)
    '흘림표': generate_toeseong,
    '느로니르': lambda tpb, dur, ch=0: generate_toeseong(tpb, dur, ch, depth=1.5),
    '느니-르': lambda tpb, dur, ch=0: generate_toeseong(tpb, dur, ch, depth=1.5),

    # 추성류 (상행 bend)
    '미는표': generate_chuseong,
    '시루표': lambda tpb, dur, ch=0: generate_chuseong(tpb, dur, ch, depth=1.5),

    # 전성류 (turn)
    '나니로': generate_jeonseong,
    '나니나': generate_jeonseong,
    '노니로': generate_jeonseong,
    '니나': lambda tpb, dur, ch=0: generate_jeonseong(tpb, dur, ch, depth=0.7),
    '니레': lambda tpb, dur, ch=0: generate_jeonseong(tpb, dur, ch, depth=0.7),
    '니레나': lambda tpb, dur, ch=0: generate_jeonseong(tpb, dur, ch, depth=1.0),
    '노라': lambda tpb, dur, ch=0: generate_jeonseong(tpb, dur, ch, depth=0.5),
    '노네': lambda tpb, dur, ch=0: generate_jeonseong(tpb, dur, ch, depth=0.5),
    '나니르노니르': lambda tpb, dur, ch=0: generate_jeonseong(tpb, dur, ch, depth=1.2),
    '너녜': lambda tpb, dur, ch=0: generate_jeonseong(tpb, dur, ch, depth=0.5),
    '노리노': lambda tpb, dur, ch=0: generate_jeonseong(tpb, dur, ch, depth=0.8),

    # 기타
    '늘임표': generate_neulim,
    '풀어내림표': generate_pulleonaelim,
    '루러표': lambda tpb, dur, ch=0: generate_chuseong(tpb, dur, ch, depth=0.8),
    '서침표': lambda tpb, dur, ch=0: generate_toeseong(tpb, dur, ch, depth=1.0),
    '끊는표': None,  # 스타카토 → velocity 조정으로 처리
    '특강표': None,  # 강조 → velocity 높임
    '반길이표': None,  # 반박 → duration 조정
}


def get_sigimsae_events(ornament_name, ticks_per_beat, duration_ticks, channel=0):
    """
    시김새 이름 → pitch bend 이벤트 리스트 반환

    Returns: (events, consumed_ticks) or (None, 0)
    """
    func = SIGIMSAE_MAP.get(ornament_name)
    if func is None:
        return None, 0
    return func(ticks_per_beat, duration_ticks, channel)


def extract_ornaments(token_name):
    """
    OMR 토큰에서 시김새 부호 추출
    예: '청황_흘림표' → ['흘림표']
        '태_나니로_흘림표' → ['나니로', '흘림표']
        '겹요성표' → ['겹요성표']
    """
    ornaments_found = []
    all_ornaments = sorted(SIGIMSAE_MAP.keys(), key=len, reverse=True)  # 긴 것 먼저

    remaining = token_name
    for orn in all_ornaments:
        if '_' + orn in remaining or remaining == orn:
            ornaments_found.append(orn)
            remaining = remaining.replace('_' + orn, '').replace(orn, '')

    return ornaments_found


if __name__ == "__main__":
    # 테스트: 각 시김새 타입별 bend 커브 시각화
    print("🎵 시김새 Pitch Bend 모듈")
    print(f"   지원 시김새: {len([k for k,v in SIGIMSAE_MAP.items() if v])}종")
    print(f"   매핑 목록:")
    for name, func in SIGIMSAE_MAP.items():
        if func:
            events, ticks = func(480, 480, 0)
            bends = [e.pitch for e in events if e.type == 'pitchwheel']
            print(f"   {name:20s} → {len(events):3d} events, "
                  f"range [{min(bends):+5d} ~ {max(bends):+5d}]")
        else:
            print(f"   {name:20s} → (velocity/duration 처리)")
