from MaliciousGroup import irc_bot


class CustomBot(irc_bot.Bot):
    def __init__(self):
        irc_bot.Bot.__init__(self)
        self._valid = "123456"

    def custom_handler(self, full: str, prefix: str, command: str, params: str, trailing: str):
        if command.lower() == "privmsg":
            if trailing.startswith(" :auth "):
                code = trailing.split(":auth ")
                if code[1] and code[1] == self._valid:
                    if prefix not in self._opers:
                        self._opers.append(prefix)
                    for chan in self._channels:
                        self.irc_message(chan, "Access Granted to {}".format(prefix.split("!")[0]))
            elif trailing.startswith(" :!rand_string "):
                if prefix not in self._opers:
                    self.irc_message(params, "Access Denied")
                    return
                try:
                    length = trailing.split(":!rand_string ")
                    if length[1]:
                        if int(length[1]) in range(1, 255):
                            self.irc_message(params, self._random_string(int(length[1])))
                except ValueError:
                    return


if __name__ == '__main__':
    my_bot = CustomBot()
    my_bot.host = "irc.blackcatz.org"
    my_bot.port = "6697"
    my_bot.channel = "#malgroup"
    my_bot.connect()
