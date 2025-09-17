from CardGames.Classes.Card import Card
from CardGames.Classes.Player import Player

class AI21(Player):
    _THRESHOLDS = {
        'weak':   0.50,
        'medium': 0.40,
        'strong': 0.28,
    }

    def _opponent_category(self, opponent_total):
        if opponent_total is None:
            return 'medium'
        if opponent_total > 21 or opponent_total <= 13:
            return 'weak'
        if 14 <= opponent_total <= 17:
            return 'medium'
        # 18–21
        return 'strong'

    def _build_remopponentning_counts(self, seen_cards):
        counts = dict((r, 4) for r in Card.ranks)
        if seen_cards:
            for c in seen_cards:
                if c and c.rank in counts and counts[c.rank] > 0:
                    counts[c.rank] -= 1
        return counts

    def _safe_and_improving_stats(self, current_total, counts):
        safe_cnt = 0
        improving_cnt = 0
        total_cnt = 0
        for r in Card.ranks:
            cnt = counts.get(r, 0)
            if cnt <= 0:
                continue
            pts = Card.points21_map[r]
            total_cnt += cnt
            new_total = current_total + pts
            if new_total <= 21:
                safe_cnt += cnt
                if 18 <= new_total <= 21:
                    improving_cnt += cnt
        return safe_cnt, total_cnt, improving_cnt

    def _adjust_threshold_for_context(self, base_threshold, total, opponent_total):
        th = base_threshold

        # Hand-shape nudges
        if total in (10, 11):
            th -= 0.05
        if total == 14:
            th += 0.02
        if total == 15:
            th += 0.05
        if total == 16:
            th += 0.10

        if opponent_total is not None:
            if opponent_total > 21:
                th += 0.08
            elif opponent_total >= 18:
                th -= 0.08
            elif opponent_total <= 13:
                th += 0.05

        # Clip
        if th < 0.0: th = 0.0
        if th > 0.95: th = 0.95
        return th

    def decide(self, seen_cards=None, opponent_total=None):
        total = self.total21()

        # Hard edges
        if total >= 21:
            return 'p'
        if total <= 9:
            return 'h'
        if total >= 17:
            return 'p'

        if seen_cards is None:
            seen_cards = list(self.hand)

        counts = self._build_remopponentning_counts(seen_cards)
        safe_cnt, total_cnt, improving_cnt = self._safe_and_improving_stats(total, counts)
        safe_prob = (float(safe_cnt) / float(total_cnt)) if total_cnt else 0.0

        opp_cat = self._opponent_category(opponent_total)
        base = self._THRESHOLDS[opp_cat]
        threshold = self._adjust_threshold_for_context(base, total, opponent_total)

        if total_cnt > 0:
            improve_prob = float(improving_cnt) / float(total_cnt)
            if improve_prob < 0.12:
                threshold += 0.02
            elif improve_prob > 0.30:
                threshold -= 0.02

        return 'h' if safe_prob >= threshold else 'p'