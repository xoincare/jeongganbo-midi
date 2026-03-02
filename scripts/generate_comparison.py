#!/usr/bin/env python3
"""
정간보 vs 오선보 vs MIDI 피아노롤 비교 이미지 생성

수제천 첫 장단을 3가지 표기법으로 나란히 보여줌
"""

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import FancyBboxPatch
import numpy as np
import os

# 한글 폰트 설정
for font_path in ['/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc',
                   '/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc',
                   '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf']:
    if os.path.exists(font_path):
        from matplotlib import font_manager
        font_manager.fontManager.addfont(font_path)
        prop = font_manager.FontProperties(fname=font_path)
        plt.rcParams['font.family'] = prop.get_name()
        break

# 수제천 제1장 첫 9정간 (피리 파트, OMR 기반 골격음)
# 남-청태-청태-청고-청태-청임 (실제 OMR 데이터에서 추출)
NOTES = [
    {'yul': '南', 'roman': 'nam', 'western': 'C5', 'midi': 72, 'dur': 2, 'beat': 0},
    {'yul': '清太', 'roman': 'cheongtae', 'western': 'F5', 'midi': 77, 'dur': 1, 'beat': 2},
    {'yul': '—', 'roman': 'tie', 'western': '', 'midi': 77, 'dur': 3, 'beat': 3},  # 지속
    {'yul': '清太', 'roman': 'cheongtae', 'western': 'F5', 'midi': 77, 'dur': 1, 'beat': 6},
    {'yul': '清姑', 'roman': 'cheonggo', 'western': 'G5', 'midi': 79, 'dur': 1, 'beat': 7},
    {'yul': '清太', 'roman': 'cheongtae', 'western': 'F5', 'midi': 77, 'dur': 1, 'beat': 8},
    {'yul': '清林', 'roman': 'cheonglim', 'western': 'Bb5', 'midi': 82, 'dur': 2, 'beat': 9},
    {'yul': '中清黃', 'roman': 'jungcheonghwang', 'western': 'Eb6', 'midi': 87, 'dur': 1, 'beat': 11},
    {'yul': '清南', 'roman': 'cheongnam', 'western': 'C6', 'midi': 84, 'dur': 1, 'beat': 12},
]

def draw_jeongganbo(ax):
    """정간보 (칸 기반 전통 악보)"""
    ax.set_title('정간보 (井間譜)', fontsize=14, fontweight='bold', pad=10)
    ax.set_xlim(-0.5, 2.5)
    ax.set_ylim(-0.5, 13.5)
    ax.invert_yaxis()
    ax.set_aspect('equal')
    ax.axis('off')

    # 정간 칸 그리기 (위→아래, 오른쪽→왼쪽 읽음)
    cell_w, cell_h = 2, 1
    yul_chars = ['南', '—', '清太', '—', '—', '—', '清太', '清姑', '清太', '清林', '—', '中清黃', '清南']

    for i, yul in enumerate(yul_chars):
        y = i
        rect = patches.Rectangle((0, y), cell_w, cell_h,
                                  linewidth=1.5, edgecolor='black', facecolor='#FFF8E7')
        ax.add_patch(rect)

        if yul == '—':
            # 이전 음 지속 표시
            ax.text(cell_w/2, y + cell_h/2, '—', ha='center', va='center',
                    fontsize=14, color='#888888')
        else:
            ax.text(cell_w/2, y + cell_h/2, yul, ha='center', va='center',
                    fontsize=13, fontweight='bold', color='#2C1810')

    # 장단 번호
    ax.text(cell_w/2, -0.3, '제1장', ha='center', va='center', fontsize=10, color='#666')


def draw_western(ax):
    """오선보 (5선 서양 악보 스타일)"""
    ax.set_title('오선보 (五線譜)', fontsize=14, fontweight='bold', pad=10)
    ax.set_xlim(-0.5, 13.5)
    ax.set_ylim(60, 95)
    ax.set_xlabel('정간 (Beat)', fontsize=10)
    ax.set_ylabel('MIDI Note', fontsize=10)

    # 5선 그리기 (treble clef 영역)
    staff_lines = [64, 67, 71, 74, 77]  # E4, G4, B4, D5, F5 근사
    for line in staff_lines:
        ax.axhline(y=line, color='#CCCCCC', linewidth=0.8, linestyle='-')

    # 보조선
    for line in [60, 81, 84, 88]:
        ax.axhline(y=line, color='#EEEEEE', linewidth=0.5, linestyle='--')

    # 음표 그리기
    colors = {'nam': '#E74C3C', 'cheongtae': '#3498DB', 'cheonggo': '#2ECC71',
              'cheonglim': '#9B59B6', 'jungcheonghwang': '#F39C12', 'cheongnam': '#1ABC9C'}

    for note in NOTES:
        if note['yul'] == '—':
            continue
        x = note['beat']
        y = note['midi']
        dur = note['dur']
        color = colors.get(note['roman'], '#333333')

        # 음표 머리
        circle = patches.Ellipse((x + dur/2, y), dur * 0.8, 2.5,
                                  facecolor=color, edgecolor='black', linewidth=1, alpha=0.8)
        ax.add_patch(circle)

        # 율명 라벨
        ax.text(x + dur/2, y + 3.5, note['yul'], ha='center', va='bottom',
                fontsize=7, color=color, fontweight='bold')

    ax.set_yticks([72, 77, 79, 82, 84, 87])
    ax.set_yticklabels(['C5\n(南)', 'F5\n(清太)', 'G5\n(清姑)', 'Bb5\n(清林)', 'C6\n(清南)', 'Eb6\n(中清黃)'],
                       fontsize=7)
    ax.grid(axis='x', alpha=0.3)


def draw_piano_roll(ax):
    """MIDI 피아노롤"""
    ax.set_title('MIDI Piano Roll', fontsize=14, fontweight='bold', pad=10)
    ax.set_xlim(-0.5, 13.5)
    ax.set_ylim(60, 95)
    ax.set_xlabel('정간 (Beat)', fontsize=10)
    ax.set_ylabel('MIDI Note #', fontsize=10)

    # 피아노 키 배경
    for midi_note in range(60, 96):
        # 검은 건반 (반음)
        is_black = (midi_note % 12) in [1, 3, 6, 8, 10]
        color = '#F0F0F0' if is_black else '#FAFAFA'
        ax.axhspan(midi_note - 0.5, midi_note + 0.5, color=color, alpha=0.5)

    # MIDI 노트 바 그리기
    bar_colors = ['#E74C3C', '#3498DB', '#3498DB', '#2ECC71', '#3498DB',
                  '#9B59B6', '#F39C12', '#1ABC9C']

    actual_notes = [n for n in NOTES if n['yul'] != '—']
    # 타이 처리: 남(2) + 청태(1+3=4) + 청태(1) + 청고(1) + 청태(1) + 청림(2) + 중청황(1) + 청남(1)
    rendered = [
        (0, 72, 2, '#E74C3C'),      # 南
        (2, 77, 4, '#3498DB'),       # 清太 (tie 포함)
        (6, 77, 1, '#3498DB'),       # 清太
        (7, 79, 1, '#2ECC71'),       # 清姑
        (8, 77, 1, '#3498DB'),       # 清太
        (9, 82, 2, '#9B59B6'),       # 清林
        (11, 87, 1, '#F39C12'),      # 中清黃
        (12, 84, 1, '#1ABC9C'),      # 清南
    ]

    for x, y, dur, color in rendered:
        rect = FancyBboxPatch((x + 0.05, y - 0.4), dur - 0.1, 0.8,
                               boxstyle="round,pad=0.05",
                               facecolor=color, edgecolor='white', linewidth=1, alpha=0.9)
        ax.add_patch(rect)

        # velocity 표시 (가운데)
        ax.text(x + dur/2, y, f'{y}', ha='center', va='center',
                fontsize=6, color='white', fontweight='bold')

    ax.set_yticks([72, 77, 79, 82, 84, 87])
    ax.set_yticklabels(['72 (C5)', '77 (F5)', '79 (G5)', '82 (Bb5)', '84 (C6)', '87 (Eb6)'],
                       fontsize=7)
    ax.grid(axis='x', alpha=0.3, color='#DDD')
    ax.grid(axis='y', alpha=0.2, color='#EEE')


def draw_mapping_table(ax):
    """12율명 → MIDI 매핑 테이블"""
    ax.set_title('12율명 ↔ MIDI 매핑 (황종=Eb4)', fontsize=14, fontweight='bold', pad=10)
    ax.axis('off')

    headers = ['율명', '한자', '서양음', 'MIDI#', '반음']
    data = [
        ['황(黃)', '黃鐘', 'Eb4', '63', '0'],
        ['대(大)', '大呂', 'E4',  '64', '+1'],
        ['태(太)', '太簇', 'F4',  '65', '+2'],
        ['협(夾)', '夾鐘', 'F#4', '66', '+3'],
        ['고(姑)', '姑洗', 'G4',  '67', '+4'],
        ['중(仲)', '仲呂', 'Ab4', '68', '+5'],
        ['유(蕤)', '蕤賓', 'A4',  '69', '+6'],
        ['임(林)', '林鐘', 'Bb4', '70', '+7'],
        ['이(夷)', '夷則', 'B4',  '71', '+8'],
        ['남(南)', '南呂', 'C5',  '72', '+9'],
        ['무(無)', '無射', 'Db5', '73', '+10'],
        ['응(應)', '應鐘', 'D5',  '74', '+11'],
    ]

    table = ax.table(cellText=data, colLabels=headers, loc='center',
                     cellLoc='center', colWidths=[0.2, 0.2, 0.2, 0.15, 0.15])
    table.auto_set_font_size(False)
    table.set_fontsize(9)
    table.scale(1, 1.4)

    # 헤더 색상
    for j in range(len(headers)):
        table[0, j].set_facecolor('#2C3E50')
        table[0, j].set_text_props(color='white', fontweight='bold')

    # 행 교대 색상
    for i in range(1, len(data) + 1):
        color = '#ECF0F1' if i % 2 == 0 else '#FFFFFF'
        for j in range(len(headers)):
            table[i, j].set_facecolor(color)


def main():
    outdir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'docs', 'images')
    os.makedirs(outdir, exist_ok=True)

    # 1) 3-way 비교 이미지
    fig, axes = plt.subplots(1, 3, figsize=(18, 10))
    fig.suptitle('수제천(壽齊天) 제1장 — 정간보 vs 오선보 vs MIDI', fontsize=16, fontweight='bold', y=0.98)

    draw_jeongganbo(axes[0])
    draw_western(axes[1])
    draw_piano_roll(axes[2])

    plt.tight_layout(rect=[0, 0, 1, 0.95])
    path1 = os.path.join(outdir, 'comparison_sujecheon.png')
    fig.savefig(path1, dpi=150, bbox_inches='tight', facecolor='white')
    plt.close()
    print(f"✅ {path1}")

    # 2) 12율명 매핑 테이블
    fig2, ax2 = plt.subplots(1, 1, figsize=(8, 7))
    draw_mapping_table(ax2)
    plt.tight_layout()
    path2 = os.path.join(outdir, 'yulname_midi_mapping.png')
    fig2.savefig(path2, dpi=150, bbox_inches='tight', facecolor='white')
    plt.close()
    print(f"✅ {path2}")

    # 3) 파이프라인 다이어그램 (텍스트 기반)
    fig3, ax3 = plt.subplots(1, 1, figsize=(14, 4))
    ax3.axis('off')
    ax3.set_xlim(0, 10)
    ax3.set_ylim(0, 3)

    boxes = [
        (0.5, 1.5, '정간보 PDF\n(스캔 이미지)', '#E8D5B7'),
        (2.5, 1.5, 'OMR 인식\n(89% 정확도)', '#AED6F1'),
        (4.5, 1.5, '율명 시퀀스\n(텍스트)', '#A9DFBF'),
        (6.5, 1.5, '파싱 & 매핑\n(12율→MIDI)', '#F9E79F'),
        (8.5, 1.5, 'MIDI 파일\n(멀티트랙)', '#D7BDE2'),
    ]

    for x, y, text, color in boxes:
        box = FancyBboxPatch((x - 0.7, y - 0.6), 1.4, 1.2,
                              boxstyle="round,pad=0.1",
                              facecolor=color, edgecolor='#333', linewidth=2)
        ax3.add_patch(box)
        ax3.text(x, y, text, ha='center', va='center', fontsize=10, fontweight='bold')

    # 화살표
    for i in range(4):
        x1 = boxes[i][0] + 0.7
        x2 = boxes[i+1][0] - 0.7
        ax3.annotate('', xy=(x2, 1.5), xytext=(x1, 1.5),
                     arrowprops=dict(arrowstyle='->', color='#555', lw=2))

    ax3.set_title('정간보 → MIDI 변환 파이프라인', fontsize=14, fontweight='bold')
    path3 = os.path.join(outdir, 'pipeline.png')
    fig3.savefig(path3, dpi=150, bbox_inches='tight', facecolor='white')
    plt.close()
    print(f"✅ {path3}")


if __name__ == "__main__":
    main()
