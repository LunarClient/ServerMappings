// DolphinMC — bot Discord con il comando /dolphinsay
require('dotenv').config();

const {
  Client,
  GatewayIntentBits,
  REST,
  Routes,
  SlashCommandBuilder,
} = require('discord.js');

// Registriamo la definizione del comando /dolphinsay
const commands = [
  new SlashCommandBuilder()
    .setName('dolphinsay')
    .setDescription('DolphinMC ti saluta')
    .toJSON(),
];

// Logica del comando, separata per poterla testare senza Discord
async function handleInteraction(interaction) {
  if (!interaction.isChatInputCommand()) return;
  if (interaction.commandName === 'dolphinsay') {
    await interaction.reply('Ciao ha funzionato!');
  }
}

// Le slash command non richiedono intent privilegiati: basta Guilds
const client = new Client({ intents: [GatewayIntentBits.Guilds] });
client.on('interactionCreate', handleInteraction);

async function main() {
  const TOKEN = process.env.DISCORD_TOKEN;
  const CLIENT_ID = process.env.CLIENT_ID;

  if (!TOKEN || !CLIENT_ID) {
    console.error('❌ Manca DISCORD_TOKEN o CLIENT_ID nel file .env (vedi .env.example)');
    process.exit(1);
  }

  try {
    // 1) Registriamo il comando globalmente (vale per tutti i server del bot)
    const rest = new REST({ version: '10' }).setToken(TOKEN);
    console.log('⏳ Registrazione del comando /dolphinsay...');
    await rest.put(Routes.applicationCommands(CLIENT_ID), { body: commands });
    console.log('✅ Comando registrato (può servire qualche minuto per vederlo apparire).');

    // 2) Login del bot
    await client.login(TOKEN);
    console.log(`✅ DolphinMC online come ${client.user.tag}`);
  } catch (err) {
    console.error('❌ Errore:', err.message || err);
    process.exit(1);
  }
}

// Avvia solo se eseguito direttamente (non quando importato da un test)
if (require.main === module) main();

module.exports = { commands, handleInteraction, client };
