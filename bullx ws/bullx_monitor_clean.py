#!/usr/bin/env python3

import websocket
import json
import os
from dotenv import load_dotenv
from datetime import datetime
import requests
import time
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

load_dotenv()

class BullXMonitor:
    def __init__(self):
        self.bearer_token = os.getenv('BULLX_BEARER_TOKEN')
        self.ws_url = "wss://stream.bullx.io/app/prowess-frail-sensitive?protocol=7&client=js&version=8.4.0-rc2&flash=false"
        self.ws = None
        self.seen_addresses = set()
        self.paused = False
        self.pending_tokens = []
        self.network_blocked = False

        
    def on_message(self, ws, message):
        try:
            data = json.loads(message)
            if data.get('event') == 'pusher:connection_established':
                # print("✅ Connexion Pusher établie")
                return
            if data.get('event') == 'pusher:subscription_succeeded':
                # print("✅ Abonnement au canal réussi")
                return
            if 'event' in data and 'new-pairs' in data['event']:
                if 'data' in data:
                    if isinstance(data['data'], str):
                        tokens_data = json.loads(data['data'])
                    else:
                        tokens_data = data['data']
                    if isinstance(tokens_data, list):
                        for token in tokens_data:
                            self.handle_token(token)
                    else:
                        self.handle_token(tokens_data)
        except Exception:
            pass

    def handle_token(self, token):
        address = self.safe_get(token, 'a', 'N/A')
        if self.paused:
            if address not in [self.safe_get(t, 'a', 'N/A') for t in self.pending_tokens]:
                self.pending_tokens.append(token)
            return
        if address in self.seen_addresses:
            return
        self.display_token(token)

    def on_error(self, ws, error):
        print(f"❌ Erreur WebSocket: {error}")
    
    def on_close(self, ws, close_status_code, close_msg):
        print("🔌 Connexion fermée")
    
    def on_open(self, ws):
        print("✅ Connexion WebSocket établie avec BullX")
        print("🔍 Surveillance des nouveaux tokens...")
        print("-" * 60)
        
        subscribe_message = {
            "event": "pusher:subscribe",
            "data": {
                "channel": "new-pairsv3-1399811149"
            }
        }
        ws.send(json.dumps(subscribe_message))
        
    def safe_get(self, token, key, default=None):
        try:
            value = token.get(key, default)
            if value is None or value == 0 or value == "":
                return default
            return value
        except:
            return default
    
    def get_bullx_price(self, address):
        try:
            url = "https://api-neo.bullx.io/v2/api/getTechnicalsV2"
            
            headers = {
                "Content-Type": "application/json",
                "Accept": "application/json, text/plain, */*",
                "Origin": "https://neo.bullx.io",
                "Referer": "https://neo.bullx.io/",
                "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36",
                "Authorization": f"Bearer {os.getenv('BULLX_BEARER_TOKEN')}"
            }
            
            payload = {
                "name": "getTechnicalsV2",
                "data": {
                    "tokenAddress": address,
                    "chainId": 1399811149
                }
            }

            response = requests.post(url, headers=headers, json=payload, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                if 'data' in data and 'tokenStats' in data['data'] and data['data']['tokenStats']:
                    token_stat = data['data']['tokenStats'][-1]
                    if 'priceNative' in token_stat:
                        price_native = token_stat['priceNative']
                        return float(price_native) if price_native else None
                
                return None
            else:
                return None
                
        except Exception:
            return None

    def get_jupiter_price(self, address):
        try:
            url = f"https://api.jup.ag/price/v2?ids={address}"
            resp = requests.get(url, timeout=5)
            
            if resp.status_code == 200:
                data = resp.json()
                if 'data' in data and address in data['data']:
                    price_str = data['data'][address]['price']
                    price = float(price_str) if price_str else None
                    return price, None, None
            return None, None, None
        except:
            return None, None, None

    def active_monitoring_multi(self, address, platform, symbol):
        print(f"🔍 Surveillance du token {symbol} ({address[:8]}...)")
        
        price_sol = None

        for attempt in range(30):
            print("📡 Requete BullX...")
            price_sol = self.get_bullx_price(address)
            
            if price_sol:
                print(f"💰 Prix BullX: {price_sol:.15f} SOL")
            
            time.sleep(1)
        
        if price_sol:
            print(f"✅ Prix récupéré avec succès via BullX: {price_sol:.8f} SOL")

        else:
            print("❌ Impossible de recuperer le prix")
        
        print("✅ Surveillance terminée - Retour au monitoring WebSocket\n")
        self.paused = False
        self.pending_tokens = []
        if self.ws:
            try:
                self.ws.close()
            except Exception:
                pass
        # print("🔄 Redémarrage complet du monitoring WebSocket...")
        time.sleep(1)
        self.start_monitoring()

    def display_token(self, token):
        try:
            # print(f"\n🔍 RÉPONSE BRUTE DU TOKEN:")
            # print(json.dumps(token, indent=2))
            # print("-" * 60)
            
            address = self.safe_get(token, 'a', 'N/A')
            if address in self.seen_addresses:
                return
            self.seen_addresses.add(address)
            timestamp = datetime.now().strftime("%H:%M:%S")
            print(f"\n🚀 [{timestamp}] NOUVEAU TOKEN")
            print("=" * 50)
            price = self.safe_get(token, 'l', None)
            secure = self.safe_get(token, 'r', 'N/A')
            name = self.safe_get(token, 'aa', 'N/A')
            symbol = self.safe_get(token, 'b', 'N/A')
            platform = self.safe_get(token, 'z', 'N/A')
            print(f"📛 {name}")
            print(f"🔤 ${symbol}")
            print(f"📍 {address}")
            if price is not None:
                print(f"💰 {price} SOL")
            else:
                print(f"💰 Prix non disponible")
            print(f"🏛️  {platform}")
            print(f"🔒 {secure}")
            print("=" * 50)
            if not self.network_blocked:
                self.paused = True
                self.active_monitoring_multi(address, platform, symbol)
            else:
                print("ℹ️  Mode surveillance seule (pas de vérification de prix)")
        except Exception:
            print(f"\n🚀 [{datetime.now().strftime('%H:%M:%S')}] Nouveau token détecté")

    def start_monitoring(self):
        headers = [
            "Origin: https://neo.bullx.io",
            "User-Agent: Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36",
        ]
        
        print("🚀 Monitoring BullX - Nouveaux Tokens")
        print(f"🔑 Token configuré: {'✅' if self.bearer_token else '❌'}")
        print(f"🌐 {self.ws_url}")
        print("")
        
        self.ws = websocket.WebSocketApp(
            self.ws_url,
            header=headers,
            on_message=self.on_message,
            on_error=self.on_error,
            on_close=self.on_close,
            on_open=self.on_open
        )
        
        self.ws.run_forever()

def main():
    monitor = BullXMonitor()
    
    try:
        monitor.start_monitoring()
    except KeyboardInterrupt:
        print("\n⏹️  Arrêt du monitoring...")
    except Exception as e:
        print(f"❌ Erreur: {e}")
    finally:
        if monitor.network_blocked:
            print("🔌 Monitoring arrêté à cause d'un blocage réseau.")

if __name__ == "__main__":
    main()
