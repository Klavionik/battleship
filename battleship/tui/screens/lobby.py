from typing import Any

import inject
from loguru import logger
from textual import on, work
from textual.app import ComposeResult
from textual.containers import Container, VerticalScroll
from textual.events import Mount, ScreenResume, Unmount
from textual.screen import Screen
from textual.widgets import Footer, Label, ListItem, ListView, Markdown

from battleship.client import Client, ClientError
from battleship.tui import resources, screens
from battleship.tui.widgets import LobbyHeader


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
                yield LobbyHeader(nickname=self._nickname)

                with ListView():
                    yield ListItem(Label("🎯 Create game"), id="create_game")
                    yield ListItem(Label("🔍 Join game"), id="join_game")
                    yield ListItem(Label("📜 Statistics"), id="stats")
                    yield ListItem(Label("👋 Logout"), id="logout")

        yield Footer()

    def action_back(self) -> None:
        self.app.switch_screen(screens.MainMenu())

    @on(Mount)
    def on_mount(self) -> None:
        self.query_one(ListView).focus()
        self.fetch_players_online()

    @on(ScreenResume)
    def update_online_count(self) -> None:
        self.fetch_players_online()

    @work(exclusive=True)
    async def fetch_players_online(self) -> None:
        try:
            count = await self._client.fetch_clients_online()
        except ClientError as exc:
            logger.exception("Cannot fetch online players count. {exc}", exc=exc)
        else:
            self.query_one(LobbyHeader).players_online = count

    @on(Unmount)
    async def disconnect_ws(self) -> None:
        await self._client.disconnect()

    @on(ListView.Selected, item="#logout")
    async def logout(self) -> None:
        await self._client.disconnect()
        await self._client.logout()
        self.action_back()

    @on(ListView.Selected, item="#create_game")
    def create_game(self) -> None:
        self.app.push_screen(screens.CreateGame())

    @on(ListView.Selected, item="#join_game")
    async def join_game(self) -> None:
        await self.app.push_screen(screens.JoinGame())

    @on(ListView.Selected, item="#stats")
    async def show_statistics(self) -> None:
        self.loading = True  # noqa

        try:
            statistics = await self._client.fetch_statistics()
            await self.app.push_screen(screens.Statistics(data=statistics))
        except ClientError:
            self.notify(
                "Cannot load statistics", title="Loading error", severity="error", timeout=5
            )
        finally:
            self.loading = False  # noqa
