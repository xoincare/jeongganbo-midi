# 정간보 → MIDI 변환기 (Jeongganbo-to-MIDI Converter)

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Songs](https://img.shields.io/badge/곡%20수-85곡-green.svg)](#-변환-결과)

> 한국 전통 궁중음악의 **정간보(井間譜)** 표기법을 **MIDI**로 변환하는 최초의 오픈소스 파이프라인

![Pipeline](docs/images/pipeline.png)

## 🎵 정간보란?

**정간보(井間譜)**는 세종대왕이 1447년 창안한 동양 최초의 유량악보(有量樂譜)입니다. 우물 정(井)자 모양의 칸에 율명(律名)을 적어 음높이와 박자를 동시에 표기합니다.

| 특징 | 정간보 | 오선보 |
|------|--------|--------|
| 읽는 방향 | 위→아래, 오른쪽→왼쪽 | 왼쪽→오른쪽 |
| 음높이 | 12율명 (黃太仲林...) | 음자리표 + 음표 위치 |
| 박자 | 칸(정간) 개수 = 박수 | 음표 모양 (♩♪♫) |
| 장식음 | 시김새 부호 (요성, 퇴성 등) | 트릴, 글리산도 등 |

## 📊 변환 예시: 수제천(壽齊天) 제1장

수제천은 백제 정읍사에서 유래한 한국 최고(最古)의 관악 합주곡(계면조)입니다.

아래는 수제천 첫 장단의 **정간보 → 오선보 → MIDI 피아노롤** 비교입니다:

![Comparison](docs/images/comparison_sujecheon.png)

**왼쪽**: 정간보 원본 — 칸 안의 한자가 율명(음높이), 칸 수가 박자  
**가운데**: 서양 음고-시간 표기 — 같은 선율을 음높이(Y축) × 시간(X축)으로 표현  
**오른쪽**: MIDI 피아노롤 — DAW에서 보이는 최종 결과물

## 🎹 12율명 ↔ MIDI 매핑

한국 전통 12율(十二律)을 MIDI 노트 번호로 변환합니다. 황종(黃鐘) 기준음은 선택 가능합니다.

![Mapping](docs/images/yulname_midi_mapping.png)

| 기준음 설정 | 황종 = | 용도 |
|-------------|--------|------|
| `hwang_pitch=63` | Eb4 | 궁중 정악 (기본값) |
| `hwang_pitch=60` | C4 | 현대 교육용 |
| `hwang_pitch=58` | Bb3 | 향악/민속악 |

### 옥타브 표기

| 접두사 | 의미 | 옥타브 | 예시 |
|--------|------|--------|------|
| (없음) | 기본 | 0 | 黃 = Eb4 (MIDI 63) |
| 청(淸) | 맑은 소리 | +1 | 清黃 = Eb5 (MIDI 75) |
| 중청(重淸) | 더 맑은 | +2 | 重清黃 = Eb6 (MIDI 87) |
| 배(倍) | 낮은 소리 | -1 | 倍黃 = Eb3 (MIDI 51) |

## 📦 변환 결과

**85곡**의 한국 궁중정악을 정간보 OMR 데이터에서 MIDI로 변환했습니다.

| 항목 | 수치 |
|------|------|
| 변환 곡 수 | **85곡** |
| 총 음표 수 | **105,626개** |
| 총 재생시간 | **89.4시간** |
| 트랙 구성 | 4~6트랙 (대금/피리/해금/아쟁/가야금/거문고) |
| OMR 정확도 | ~89% (MALerLab jeongganbo-omr 기반) |

### 포함 레퍼토리

| 분류 | 곡목 | 곡수 |
|------|------|------|
| 영산회상 | 상령산, 중령산, 세령산, 가락덜이, 상현도드리, 염불도드리, 타령, 군악, 하현도드리 | 9 |
| 관악영산회상 | 상령산~군악 (위와 같은 구성) | 8 |
| 평조회상 | 상령산~타령 | 8 |
| 수제천(壽齊天) | 백제 최고(最古) 관악합주 | 1 |
| 여민락(與民樂) | 세종대왕 작곡, 14,052 notes | 1 |
| 동동(動動) | 고려가요 기악곡 | 1 |
| 남창 가곡 | 우조/계면 초수대엽~태평가 | 20+ |
| 여창 가곡 | 우조/계면 | 8 |
| 취타/현악취타 | 군악, 길군악, 길타령, 별우조타령 | 9 |
| 자진한잎 | 경풍년, 수룡음, 염양춘 | 7 |
| 천년만세 | 양청/계면/우조 가락도드리 | 3 |
| 밑도드리/웃도드리 | 관현악 합주 | 2 |

### 악기별 GM MIDI 매핑

| 국악기 | GM Instrument | GM# | 옥타브 보정 |
|--------|---------------|-----|-------------|
| 대금 (大笒) | Flute | 73 | +1 |
| 피리 (觱篥) | Oboe | 68 | 0 |
| 해금 (奚琴) | Fiddle | 110 | 0 |
| 아쟁 (牙箏) | Cello | 42 | -1 |
| 가야금 (伽倻琴) | Nylon Guitar | 25 | 0 |
| 거문고 (玄琴) | Steel Guitar | 24 | -1 |

## 🚀 사용법

### 요구사항

```bash
pip install mido
```

### 단일 시퀀스 변환

```python
from scripts.jeongganbo_converter import JeongganboConverter

conv = JeongganboConverter(hwang_pitch=63)  # Eb4 기준

# 율명 시퀀스: (율명, 정간수, 옥타브)
sequence = [
    ('황', 2, 0),   # 황종 2박
    ('태', 1, 0),   # 태주 1박
    ('중', 1, 0),   # 중려 1박
    ('임', 2, 0),   # 임종 2박
    ('황', 4, 1),   # 청황종 4박 (1옥타브 위)
]

conv.sequence_to_midi(sequence, "output.mid", bpm=60)
```

### 텍스트 파싱

```python
conv = JeongganboConverter(hwang_pitch=63)
seq = conv.parse_simple_notation("황2 태 중 임2 황+1")
conv.sequence_to_midi(seq, "output.mid", bpm=60)
```

### OMR 결과 → MIDI 일괄 변환

```bash
# 싱글트랙 (모든 악기 합쳐서)
python scripts/omr_to_midi.py

# 멀티트랙 (악기별 분리)
python scripts/omr_to_midi_multitrack.py
```

## 📁 프로젝트 구조

```
jeongganbo-midi/
├── README.md
├── LICENSE
├── scripts/
│   ├── jeongganbo_converter.py    # 핵심: 율명→MIDI 변환 엔진
│   ├── omr_to_midi.py             # OMR→MIDI 싱글트랙 변환
│   ├── omr_to_midi_multitrack.py  # OMR→MIDI 멀티트랙 변환
│   ├── sujecheon_test.py          # 수제천 테스트 스크립트
│   └── generate_comparison.py     # 비교 이미지 생성
├── midi/
│   ├── single/                    # 싱글트랙 MIDI (85곡)
│   ├── multitrack/                # 멀티트랙 MIDI (85곡)
│   ├── sujecheon_piri.mid         # 수제천 피리 (수동 입력 테스트)
│   ├── sujecheon_daegeum.mid      # 수제천 대금 (수동 입력 테스트)
│   └── test_*.mid                 # 스케일/조성 테스트
└── docs/
    └── images/
        ├── comparison_sujecheon.png  # 3-way 비교
        ├── yulname_midi_mapping.png  # 12율명 매핑표
        └── pipeline.png             # 파이프라인 다이어그램
```

## ⚠️ 알려진 한계

| 한계 | 설명 | 개선 방향 |
|------|------|-----------|
| **시김새 미반영** | 요성, 퇴성, 추성 등 장식음이 MIDI에 포함되지 않음 | Pitch Bend로 구현 예정 |
| **OMR 오류** | 원본 OMR 89% 정확도 → ~11% 오인식 가능 | 수동 교정 + 모델 개선 |
| **템포 고정** | 모든 곡 BPM 25 고정 | 곡별 템포 메타데이터 추가 |
| **GM 음색 한계** | 서양 악기 음색으로 대체 | SoundFont/샘플러 연동 |

## 🔮 로드맵

- [ ] **v1.1**: 시김새(장식음) → Pitch Bend 변환
- [ ] **v1.2**: 곡별 실제 템포/장단 적용
- [ ] **v2.0**: 정간보 이미지 → MIDI 직접 변환 (End-to-End)
- [ ] **v2.1**: 웹 기반 변환 앱 (업로드 → 미리듣기 → 다운로드)
- [ ] 한국 전통 악기 SoundFont 연동
- [ ] 민속악(산조, 시나위 등) 정간보 지원

## 📚 참고

- **MALerLab/jeongganbo-omr** — 정간보 OMR 프레임워크 ([논문](https://dl.acm.org/doi/10.1145/3715159))
- **국립국악원 정악보** — 가야금/거문고/대금/아쟁/피리/해금 정악보 (2021)
- **depth221/Jeongganbo-editor** — 정간보 에디터 (율명 매핑 참조)

## 📄 라이선스

MIT License

OMR 데이터 출처: [MALerLab/jeongganbo-omr](https://github.com/MALerLab/jeongganbo-omr) (학술 연구용 데이터셋)

---

**🇰🇷 세종대왕이 1447년에 만든 악보가 2026년에 MIDI가 되었습니다.**
