# 🐬 DolphinMC

Bot Discord minimale con una sola slash command: **/dolphinsay** → risponde `Ciao ha funzionato!`

## Requisiti
- [Node.js](https://nodejs.org/) 18 o superiore
- Un'applicazione/bot creato sul [Discord Developer Portal](https://discord.com/developers/applications)

## 1. Configurazione
```bash
npm install
cp .env.example .env      # su Windows: copy .env.example .env
```
Apri `.env` e incolla:
```
DISCORD_TOKEN=il_token_del_bot
CLIENT_ID=l_application_id
```
Dove trovarli (Developer Portal → la tua app):
- **Bot** → *Reset Token* → *Copy* → `DISCORD_TOKEN`
- **General Information** → *Application ID* → `CLIENT_ID`

> ⚠️ Il token è una password: non condividerlo e non pubblicarlo su GitHub.

## 2. Avvio
```bash
npm start
```
Se tutto va bene vedrai:
```
⏳ Registrazione del comando /dolphinsay...
✅ Comando registrato
✅ DolphinMC online come DolphinMC#0000
```
Le slash command globali possono impiegare **fino a ~1 ora** per comparire su tutti i server
(trucco: chiudere e riaprire Discord con Ctrl+R / Cmd+R).

## 3. Invito del bot
Sostituisci `TUO_CLIENT_ID` e apri nel browser:
```
https://discord.com/oauth2/authorize?client_id=TUO_CLIENT_ID&scope=bot+applications.commands&permissions=2048
```
Scegli il server → Autorizza. Ora su quel server scrivi `/dolphinsay`.

## Comandi
| Comando | Risposta |
|---|---|
| `/dolphinsay` | `Ciao ha funzionato!` |

## Personalizzare la risposta
In `index.js` cerca:
```js
await interaction.reply('Ciao ha funzionato!');
```
e cambia il testo (o aggiungi `{ ephemeral: true }` per una risposta visibile solo a chi usa il comando).

## Dove tenerlo online 24/7
- Il tuo PC (deve restare accesso con `npm start` in esecuzione)
- Un VPS economico, oppure hosting gratuiti/economici tipo Railway, Render, Fly.io, Bot-Hosting
- In alternativa: `pm2 start index.js --name dolphinmc` per tenerlo vivo su un server
