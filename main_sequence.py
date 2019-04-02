from MaliciousGroup import irc_bot


class CustomBot(irc_bot.Bot):
    def custom_handler(self, full: str, prefix: str, command: str, params: str, trailing: str):
        if command.lower() == "privmsg":
            if trailing == " :!help":
                self._w_queue.put(":null PRIVMSG {} :Default Message".format(params))


if __name__ == '__main__':
    my_bot = CustomBot()
    my_bot.host = "irc.blackcatz.org"
    my_bot.port = "6697"
    my_bot.channel = "#malgroup"
    my_bot.connect()
