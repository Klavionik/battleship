from typing import Any

import inject
from textual import on
from textual.app import ComposeResult
from textual.containers import Container, VerticalScroll
from textual.events import Mount
from textual.screen import Screen
from textual.widgets import Footer, Label, ListItem, ListView, Markdown, Static

from battleship.client import Client
from battleship.tui import resources, screens


class Lobby(Screen[None]):
    BINDINGS = [("escape", "back", "Back")]

    @inject.param("client", Client)
    def __init__(self, *args: Any, nickname: str, client: Client, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self._nickname = nickname
        self._client = client

        with resources.get_resource("lobby_help.md").open() as fh:
            self.help = fh.read()

    def compose(self) -> ComposeResult:
        with Container(classes="main"):
            with VerticalScroll():
                yield Markdown(self.help, classes="screen-help")

            with Container(classes="screen-content"):
                yield Static(f"👤{self._nickname}", id="username")

                with ListView():
                    yield ListItem(Label("🎯 Create game"), id="create_game")
                    yield ListItem(Label("🔍 Join game"), id="join_game")
                    yield ListItem(Label("📜 Statistics"))
                    yield ListItem(Label("👋 Logout"), id="logout")

        yield Footer()

    def action_back(self) -> None:
        self.app.switch_screen(screens.MainMenu())

    @on(Mount)
    async def connect_ws(self) -> None:
        await self._client.connect()

    @on(ListView.Selected, item="#logout")
    async def logout(self) -> None:
        await self._client.disconnect()
        await self._client.logout()
        await self.app.switch_screen(screens.Multiplayer())

    @on(ListView.Selected, item="#create_game")
    def create_game(self) -> None:
        self.app.push_screen(screens.CreateGame())

    @on(ListView.Selected, item="#join_game")
    async def join_game(self) -> None:
        await self.app.push_screen(screens.JoinGame())
