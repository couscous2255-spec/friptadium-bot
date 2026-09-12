#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Friptadium Stock Bot - version GitHub Actions
================================================
Fait UN SEUL check de disponibilité (pas de boucle), pensé pour être
relancé automatiquement toutes les X minutes par GitHub Actions.

Ne dépend que de la bibliothèque standard Python.
Le token et le chat_id sont lus depuis des variables d'environnement
(configurées comme "secrets" GitHub), jamais écrits en clair ici.
"""

import json
import os
import sys
import urllib.request
import urllib.error

# Produits à surveiller : nom affiché -> URL Shopify .json du produit
PRODUCTS = {
    "Hauts Homme Premium": "https://friptadium.com/products/hauts-homme-premium-au-kilo.json",
    "Bas Homme Premium": "https://friptadium.com/products/bas-homme-premium-au-kilo.json",
}

STATE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "friptadium_state.json")

BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")


def send_telegram_message(text: str) -> None:
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = json.dumps({"chat_id": CHAT_ID, "text": text}).encode("utf-8")
    req = urllib.request.Request(
        url, data=data, headers={"Content-Type": "application/json"}
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            resp.read()
    except urllib.error.URLError as e:
        print(f"[!] Erreur envoi Telegram : {e}")


def is_available(product_url: str) -> bool:
    req = urllib.request.Request(
        product_url, headers={"User-Agent": "Mozilla/5.0 (stock-monitor-bot)"}
    )
    with urllib.request.urlopen(req, timeout=15) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    variants = data.get("product", {}).get("variants", [])
    return any(v.get("available") for v in variants)


def load_state() -> dict:
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            return {}
    return {}


def save_state(state: dict) -> None:
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f)


def main() -> None:
    if not BOT_TOKEN or not CHAT_ID:
        print("[!] BOT_TOKEN ou CHAT_ID manquant (secrets GitHub non configurés).")
        sys.exit(1)

    state = load_state()
    for name in PRODUCTS:
        state.setdefault(name, False)

    for name, url in PRODUCTS.items():
        try:
            available_now = is_available(url)
        except Exception as e:
            print(f"[!] Erreur en vérifiant '{name}' : {e}")
            continue

        was_available = state.get(name, False)

        if available_now and not was_available:
            product_page = url.replace(".json", "")
            message = f"🚨 {name} est DISPONIBLE !\n{product_page}"
            print(f"[+] {message}")
            send_telegram_message(message)
        elif not available_now:
            print(f"[.] {name} : toujours épuisé.")
        else:
            print(f"[.] {name} : toujours disponible (déjà notifié).")

        state[name] = available_now

    save_state(state)


if __name__ == "__main__":
    main()
