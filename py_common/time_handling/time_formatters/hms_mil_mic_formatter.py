from .time_formatter import ABCTimeFormatter


class HMSMilMicFormatter(ABCTimeFormatter):
    """
    Format: HH:MM:SS:MMMms:XXXX...µs

    - HH, MM, SS → always 2 digits
    - MMM (milliseconds) → always 3 digits
    - microsecond field width = round_digits
      * if round_digits <= 3: round the 0..999 µs remainder to that many digits (carry-safe)
      * if round_digits > 3: show 3 µs digits and pad with zeros to reach width
    - If round_digits is None → default to 6
    """

    # noinspection t
    def format(self, total_seconds: float, round_digits: int | None) -> str:
        # sign
        sign = "-" if total_seconds < 0 else ""
        if total_seconds < 0:
            total_seconds = -total_seconds

        # default width for last field
        if round_digits is None:
            round_digits = 6
        if round_digits < 0:
            round_digits = 0

        # Work in integer microseconds to avoid FP noise
        total_us = int(round(total_seconds * 1_000_000))

        # Decompose
        hours, rem_us = divmod(total_us, 3_600_000_000)
        minutes, rem_us = divmod(rem_us, 60_000_000)
        seconds, rem_us = divmod(rem_us, 1_000_000)
        ms, us = divmod(rem_us, 1_000)   # ms: 0..999, us: 0..999 (microsecond remainder)

        # Build the microsecond tail with requested width
        if round_digits <= 3:
            # Round us (0..999) to the requested number of digits (0..3), with carry
            if round_digits == 0:
                # rounding to 0 digits -> either "0" or "1" with carry if >= 500
                carry = 1 if us >= 500 else 0
                us_rounded = 0
            else:
                # e.g. width=2 -> keep top 2 digits of us (0..999), rounding the 3rd
                scale = 10 ** (3 - round_digits)    # 1, 10, or 100
                us_rounded = (us + scale // 2) // scale
                carry = 1 if us_rounded == 10 ** round_digits else 0
                if carry:
                    us_rounded = 0

            if carry:
                ms += 1
                if ms == 1000:
                    ms = 0
                    seconds += 1
                    if seconds == 60:
                        seconds = 0
                        minutes += 1
                        if minutes == 60:
                            minutes = 0
                            hours += 1

            tail = f"{us_rounded:0{round_digits}d}" if round_digits > 0 else "0"

        else:
            # width > 3: show 3 µs digits then zero-pad to desired width
            tail = f"{us:03d}" + ("0" * (round_digits - 3))

        return (
            f"{sign}"
            f"{hours:02d}H:{minutes:02d}M:{seconds:02d}S:"
            f"{ms:03d}ms:{tail}µs"
        )
