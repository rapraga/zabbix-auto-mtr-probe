#!/usr/bin/env python3

import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

# =========================
# CONFIG ZABBIX
# =========================

ZABBIX_SERVER = "IP DO SERVER ZABBIX"
ZABBIX_HOST = "MTR-AUTOMATICO"

KEY_REPORT = "mtr.report"
KEY_TRIGGER = "mtr.trigger"

CYCLES = 20
TIMEOUT = 120
MAX_THREADS = 10

# =========================
# DESTINOS
# =========================

HOSTS = [
    "globo.com",
    "uol.com.br",
    "9.9.9.9",
    "nic.br",
    "1.1.1.1",
    "208.67.222.222",
    "187.16.218.182",
    "steampowered.com",
    "x.com"
]

# =========================
# EXEC MTR + EXTRAÇÃO LOSS
# =========================

def run_mtr(target):

    print(f"[MTR] {target}")

    cmd = [
        "mtr",
        "-n",
        "-r",
        "-c", str(CYCLES),
        target
    ]

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=TIMEOUT
        )

        lines = result.stdout.splitlines()

        report = []
        report.append("\n" + "=" * 80)
        report.append(f"DESTINO: {target}")
        report.append("=" * 80)
        report.append(f"{'SALTO':<25}{'PERDA':<10}{'LATÊNCIA MÉDIA'}")

        loss_final = 0.0

        for line in lines:

            line = line.strip()

            if not line or "Loss%" in line or "Start:" in line or "HOST:" in line:
                continue

            if ".|--" not in line:
                continue

            parts = line.split()

            try:
                hop = parts[1]
                loss = parts[2].replace('%', '')
                avg = parts[5]

                report.append(f"{hop:<25}{loss + '%':<10}{avg} ms")

                # só captura perda do destino final (último hop relevante)
                loss_final = float(loss)

            except:
                continue

        return target, loss_final, "\n".join(report)

    except Exception as e:
        return target, 0.0, f"\n### {target}\nERRO: {str(e)}\n"


# =========================
# SEND ZABBIX
# =========================

def send_to_zabbix(key, value):

    subprocess.run([
        "zabbix_sender",
        "-z", ZABBIX_SERVER,
        "-s", ZABBIX_HOST,
        "-k", key,
        "-o", str(value)
    ])


# =========================
# MAIN
# =========================

def main():

    print(f"\n=== MTR INCIDENT COLLECTOR === {datetime.now()} ===\n")

    results = []
    loss_counter = 0

    with ThreadPoolExecutor(max_workers=MAX_THREADS) as executor:

        futures = [executor.submit(run_mtr, h) for h in HOSTS]

        for f in as_completed(futures):

            host, loss, report = f.result()

            results.append(report)

            # regra de decisão
            if loss >= 20.0:
                loss_counter += 1

    # =========================
    # DECISÃO FINAL
    # =========================

    trigger_value = 1 if loss_counter >= 7 else 0

    final_report = "\n".join(results)

    # envia relatório
    send_to_zabbix(KEY_REPORT, final_report)

    # envia trigger
    send_to_zabbix(KEY_TRIGGER, trigger_value)

    print("\n========================")
    print(f"HOSPS COM PERDA >=20%: {loss_counter}")
    print(f"TRIGGER ENVIADA: {trigger_value}")
    print("========================\n")


if __name__ == "__main__":
    main()
