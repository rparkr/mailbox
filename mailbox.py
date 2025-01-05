import marimo

__generated_with = "0.10.8-dev3"
app = marimo.App()


@app.cell
def _(mo):
    _title = mo.md(
        f"""# {mo.icon("noto:open-mailbox-with-raised-flag")} Mailbox: find letters within words
        Just choose a letter and its position in a word to find words that use that letter!
            """
    )
    _about = mo.accordion(
        {
            "## About this app": (
                f"""This is a simple application I made for teaching my son about letters. Typical alphabet games and books use _starts with_ for letter association, like "**A** is for **A**pple :apple:". Though helpful, I have observed that young children tend to recognize letters by _prominence_ in a word -- for example, the **g** in e**gg** is a more prominent-sounding letter than the **e**; a more prominent use of **e** might be found in tr**ee**. Other times it is valuable to recognize that letters all throughout a word are important. When we learn to speed read, we are not just looking at the first letter of a word, but rather the word as a whole, thus, all the letters are important in that word.
            
                This application shows a randomized list of words that contain a chosen letter either at the beginning, middle, or end (or a combination). The word list comes from [this GitHub repository {mo.icon("octicon:mark-github-16")}](https://github.com/first20hours/google-10000-english), the 10,000 most common English words from Google's N-gram Trillion Words corpus, filtered to exclude swear words.
                """
            )
        }
    )

    mo.vstack([_title, _about])
    return


@app.cell
def _(
    match_beginning,
    match_end,
    match_middle,
    mo,
    number_of_matches,
    refresh_button,
    selected_letter,
    toggle_match_condition,
    update_word_list,
):
    # Group elements together
    group = mo.vstack(
        [
            selected_letter,
            mo.hstack(
                [match_beginning, match_middle, match_end, toggle_match_condition],
                justify="start",
                align="center",
            ),
            number_of_matches,
            update_word_list(),
            refresh_button,
        ],
    )

    group
    return (group,)


@app.cell
def _(ALL_LETTERS, Literal, mo, pyodide, random, re):
    @mo.cache()
    def get_word_list() -> list[str]:
        """Load the list of words as a newline-delimitted string."""
        word_list_url = "https://raw.githubusercontent.com/first20hours/google-10000-english/refs/heads/master/google-10000-english-usa-no-swears.txt"

        # Use pyodide.http because other web request libraries like httpx or requests
        # might not work
        word_list = pyodide.http.open_url(word_list_url).read()
        return word_list


    def find_words(
        selected_letter: str,
        word_list: str,
        num_matches: int = 5,
        match_beginning: bool = True,
        match_middle: bool = True,
        match_end: bool = True,
        require_all: bool = False,
    ) -> list[str]:
        """Return a list of words where the given letter matches the given positions."""
        # Reference patterns for the letter Z (test them in https://regex101.com/)
        # Letter at beginning of word: "^Z.*$"
        # Letter in middle of word: "^.+Z.+$"
        # Letter at end of word: "^.+Z$"
        # Letter in all positions: "^Z.*Z.*Z$"
        # Letter in any position: "^.*Z.*$"

        patterns = {
            "beginning": f"^{selected_letter}.*",
            "middle": f"{selected_letter}.*",
            "end": f"{selected_letter}$",
        }

        if all([match_beginning, match_middle, match_end, not require_all]):
            # Can match in any position
            pattern = f"^.*{selected_letter}.*$"
        elif require_all:
            # Beginning of word
            pattern = patterns["beginning"] if match_beginning else "^.+"
            # Middle of word
            pattern += patterns["middle"] if match_middle else ".*"
            # End of word
            pattern += patterns["end"] if match_end else ".+$"
        else:
            # join with an OR condition, trimming leading and trailing "|" as needed
            pattern = (
                "|".join(
                    [
                        patterns["beginning"] + "$" if match_beginning else "",
                        "^.+" + patterns["middle"] + "$" if match_middle else "",
                        "^.+" + patterns["end"] if match_end else "",
                    ]
                )
                .replace("||", "|")
                .strip("|")
            )

        # Find all matches as a list
        matches = re.findall(
            pattern=pattern, string=word_list, flags=re.MULTILINE | re.IGNORECASE
        )
        # Return a sample of matches
        return random.sample(list(matches), k=min(num_matches, len(matches)))


    def stylize_word(
        letter: str = "",
        word: str = "",
        color: int | str | None = None,
        style_beginning: str = '<span style="color: {color_hex_value}; font-weight: bold;">',
        style_end: str = "</span>",
    ) -> str:
        """Format a word using Markdown, making the selected letter bold and colored."""
        if isinstance(color, int):
            color_hex_value = hex(color)
        elif isinstance(color, str) and color.startswith("0x"):
            color_hex_value = color
        else:
            # Choose a random color from the hexadecimal RGB color spectrum
            color_hex_value = hex(random.randint(0, 256**3))

        if "color_hex_value" in style_beginning:
            style_beginning = style_beginning.format(
                # trim the leading "0x" an add a hashtag to the hex value
                # for interpretation as a color
                color_hex_value="#"
                + color_hex_value[2:]
            )

        return (
            word.replace(
                letter.lower(), style_beginning + letter.lower() + style_end
            )
            # If a letter is repeated, omit the duplicate formatting
            .replace(style_end + style_beginning, "").lower()
        )


    def update_word_list(style: Literal["list", "slides"] = "list"):
        """Update the list of words"""
        # Choose a random color in the RGB color space
        color = hex(random.randint(0, 256**3))
        elements = [
            mo.md(
                f'# \[ <span style="color: #{color[2:]}; font-weight: bold;">{selected_letter.value}</span> \]'
            )
        ] + [
            mo.md(f"# {stylize_word(selected_letter.value, word, color=color)}")
            for word in find_words(
                selected_letter=selected_letter.value,
                word_list=word_list,
                num_matches=number_of_matches.value,
                match_beginning=match_beginning.value,
                match_middle=match_middle.value,
                match_end=match_end.value,
                require_all=not toggle_match_condition.value,
            )
        ]
        if style == "slides":
            # For a slide format:
            displayed_value = displayed_value = mo.carousel(elements)
        else:
            # For a list format:
            displayed_value = mo.vstack(
                elements,
                justify="center",
                align="stretch",
            )
        return displayed_value


    selected_letter = mo.ui.dropdown(
        label="Select a letter:", options=list(ALL_LETTERS) + [""], value=""
    )
    match_beginning = mo.ui.checkbox(value=True, label="Beginning")
    match_middle = mo.ui.checkbox(value=True, label="Middle")
    match_end = mo.ui.checkbox(value=True, label="End")
    toggle_match_condition = mo.ui.switch(
        value=True, label="match for any selected position"
    )
    number_of_matches = mo.ui.slider(
        start=1, stop=10, value=5, label="Number of words:", show_value=True
    )
    refresh_button = mo.ui.button(label="Refresh", on_click=update_word_list)

    # Load word list
    word_list = get_word_list()
    return (
        find_words,
        get_word_list,
        match_beginning,
        match_end,
        match_middle,
        number_of_matches,
        refresh_button,
        selected_letter,
        stylize_word,
        toggle_match_condition,
        update_word_list,
        word_list,
    )


@app.cell
def _():
    # import logging
    import random
    import re
    import string
    from typing import Literal

    ALL_LETTERS = string.ascii_uppercase

    import marimo as mo
    import pyodide.http

    # # Set up logging
    # logging.basicConfig(level=logging.INFO)
    # logger = logging.getLogger(__name__)
    return ALL_LETTERS, Literal, mo, pyodide, random, re, string


if __name__ == "__main__":
    app.run()
