import random
from collections import Counter
from typing import List, Tuple

# --------- 牌面權重 (A 最大) ---------
RANK_VAL = {i: i+2 for i in range(13)}  # 0->2, …, 11->13, 12->14
RANK_VAL[12] = 14                      # Ace
SUIT_VAL = {0: 3, 1: 2, 2: 1, 3: 0}    # ♠>♥>♦>♣   (0=♠)

# 牌型編號：用來決定大類型
HAND_RANK = {
    "straight_flush": 9,
    "four_kind": 8,
    "full_house": 7,
    "flush": 6,
    "straight": 5,
    "three_kind": 4,
    "two_pair": 3,
    "one_pair": 2,
    "high_card": 1,
}

# --------- 工具函式 ---------
def card_rank(c: int) -> int:
    """回傳 A=14, K=13, … 2=2"""
    return RANK_VAL[c % 13]

def card_suit(c: int) -> int:
    """0:♠ 1:♥ 2:♦ 3:♣"""
    return c // 13

def pretty(c: int) -> str:
    suit_symbols = ["♠", "♥", "♦", "♣"]
    faces = ["A"] + [str(n) for n in range(2, 11)] + ["J", "Q", "K"]
    return f"{suit_symbols[card_suit(c)]}{faces[c % 13]}"

def print_cards(cards: List[int]) -> None:
    print(" ".join(pretty(c) for c in cards))

# --------- 牌型評分 ---------
def evaluate_hand(cards: List[int]) -> int:
    """回傳一個可直接比較大小的整數分數"""
    ranks = [card_rank(c) for c in cards]
    suits = [card_suit(c) for c in cards]
    rank_counter = Counter(ranks)
    counts = sorted(rank_counter.values(), reverse=True)

    is_flush = len(set(suits)) == 1
    # 處理 A2345 直順：把 Ace 當 1 再檢查
    sorted_ranks = sorted(set(ranks))
    is_wheel = sorted_ranks == [2, 3, 4, 5, 14]
    if is_wheel:
        straight_high = 5
    else:
        straight_high = max(sorted_ranks)
    is_straight = len(sorted_ranks) == 5 and max(sorted_ranks) - min(sorted_ranks) == 4 or is_wheel

    # 判斷牌型
    if is_straight and is_flush:
        cat = "straight_flush"
        key = [straight_high]
    elif counts == [4, 1]:
        cat = "four_kind"
        four = rank_counter.most_common(1)[0][0]
        kicker = min(r for r in ranks if r != four)
        key = [four, kicker]
    elif counts == [3, 2]:
        cat = "full_house"
        three = rank_counter.most_common(1)[0][0]
        pair = rank_counter.most_common(2)[1][0]
        key = [three, pair]
    elif is_flush:
        cat = "flush"
        key = sorted(ranks, reverse=True)
    elif is_straight:
        cat = "straight"
        key = [straight_high]
    elif counts == [3, 1, 1]:
        cat = "three_kind"
        three = rank_counter.most_common(1)[0][0]
        kickers = sorted([r for r in ranks if r != three], reverse=True)
        key = [three] + kickers
    elif counts == [2, 2, 1]:
        cat = "two_pair"
        pairs = [r for r, c in rank_counter.items() if c == 2]
        high_pair, low_pair = sorted(pairs, reverse=True)
        kicker = min(r for r in ranks if r not in pairs)
        key = [high_pair, low_pair, kicker]
    elif counts == [2, 1, 1, 1]:
        cat = "one_pair"
        pair = rank_counter.most_common(1)[0][0]
        kickers = sorted([r for r in ranks if r != pair], reverse=True)
        key = [pair] + kickers
    else:
        cat = "high_card"
        key = sorted(ranks, reverse=True)

    # 花色最大者（黑桃最大）也加進去做最終 Tie-break
    max_suit = max(suits, key=lambda s: SUIT_VAL[s])

    # 組合成整數：型別 *10^8 + 主序 *10^6 + 花色 *10^4 + 其餘 kicker……
    score = HAND_RANK[cat] * 10**8 + key[0] * 10**6 + SUIT_VAL[max_suit] * 10**4
    factor = 10**3
    for k in key[1:]:
        score += k * factor
        factor //= 10
    return score

# --------- 遊戲流程 ---------
def draw(deck: List[int], n: int) -> List[int]:
    """從牌堆頂端抽 n 張（並移除）"""
    picked = deck[:n]
    del deck[:n]
    return picked

def player_choose_change(hand: List[int], deck: List[int]) -> None:
    """玩家可選擇把三張裡面換掉一張"""
    extra = draw(deck, 3)
    print("\n您抽到的三張補牌：", end="")
    print_cards(extra)
    hand += extra
    print("目前手牌：", end="")
    print_cards(hand)
    ans = input("要不要換牌？(y/n) ").strip().lower()
    if ans == "y":
        idx = int(input("請輸入要換掉的索引(0~2): "))
        if 0 <= idx <= 2:
            hand[-3 + idx] = draw(deck, 1)[0]
            print("換牌完成，最終手牌：", end="")
            print_cards(hand)
        else:
            print("索引錯誤，視同不換牌")
    else:
        print("您選擇保留補牌。")

def single_round(players: int, money: List[int]) -> None:
    deck = list(range(52))
    random.shuffle(deck)

    hands = [draw(deck, 2) for _ in range(players)]

    # 玩家輪流決定是否換牌
    for pid in range(players):
        print(f"\n=== 玩家 {pid+1} 回合 ===")
        print("目前兩張手牌：", end="")
        print_cards(hands[pid])
        player_choose_change(hands[pid], deck)

        # 自動補到五張
        hands[pid] += draw(deck, 5 - len(hands[pid]))
        print("最終五張手牌：", end="\n")
        print_cards_ascii(hands[pid])

    # 下注
    pot = 0
    for pid in range(players):
        while True:
            try:
                bet = int(input(f"\n玩家 {pid+1} (剩餘 ${money[pid]})，請下注："))
                if 0 <= bet <= money[pid]:
                    break
            except ValueError:
                pass
            print("輸入無效，請重來。")
        money[pid] -= bet
        pot += bet

    # 比牌
    scores = [evaluate_hand(h) for h in hands]
    best = max(scores)
    winners = [i for i, s in enumerate(scores) if s == best]

    print("\n=== 結果 ===")
    for pid in range(players):
        tag = "(勝者)" if pid in winners else ""
        print(f"玩家 {pid+1}: ", end="")
        print_cards(hands[pid])
        print(f"  分數={scores[pid]} {tag}")

    share = pot // len(winners)
    for w in winners:
        money[w] += share
    print(f"\n牌池 ${pot} 平分，每位勝者獲得 ${share}")

def main():
    players = int(input("請輸入玩家數量: "))
    money = [1000] * players

    round_no = 1
    while True:
        print(f"\n===== 第 {round_no} 局開始 =====")
        single_round(players, money)

        # 檢查破產
        for pid in range(players):
            if money[pid] == 0:
                print(f"玩家 {pid+1} 已破產，被淘汰。")
        if all(m == 0 for m in money):
            print("所有玩家皆破產，遊戲結束！")
            break

        cont = input("\n再玩一局？(y/n) ").strip().lower()
        if cont != "y":
            break
        round_no += 1

    print("\n=== 遊戲結束，最終資金 ===")
    for pid, cash in enumerate(money, 1):
        print(f"玩家 {pid}: ${cash}")



CARD_WIDTH = 5
SUIT_GLYPH = ["♠", "♥", "♦", "♣"]
RANK_TEXT  = ["A"] + [str(n) for n in range(2, 11)] + ["J", "Q", "K"]

def card_art(card: int) -> list[str]:
    """回傳 3 字串，分別是卡片的上、中、下三行"""
    suit = card // 13
    rank = card % 13
    rank_str = RANK_TEXT[rank]

    color = "\033[31m" if suit in (1, 2) else "\033[37m"
    reset = "\033[0m"
    face = f"{SUIT_GLYPH[suit]}{rank_str}"
    face = f"{color}{face:<3}{reset}"          # 置左補空格

    top    = f"┌{'─'*(CARD_WIDTH-2)}┐"
    middle = f"│{face}│"
    bottom = f"└{'─'*(CARD_WIDTH-2)}┘"
    return [top, middle, bottom]

def print_cards_ascii(cards):
    """橫向並排顯示多張牌"""
    arts = [card_art(c) for c in cards]
    for row in range(3):                       # 3 行
        print(" ".join(a[row] for a in arts))

if __name__ == "__main__":
    main()

