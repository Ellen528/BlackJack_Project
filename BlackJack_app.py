"""Program: 
    1. Create a blackjack game with the following classes:
        - Card: Represents a card in the deck.
        - Joker: Represents a deck of cards.
        - Player: Represents a player in the game.
        - Dealer: Represents the dealer in the game.
        - Gumbler: Represents the player in the game.
    2. Functions to play one round of the game.
    3. Functions to calculate the winner of n rounds of the game.
    4. Functions to plot the strategy report with the player and dealer win rates and Luck distribution graph for the player.
    5. Functions to create a web page of the blackjack game in streamlit.
    Author: Shuang Yan
    Date: 2024-05-24
"""

import random
import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import binom

# ===== Blackjack Game Logic =====
class Card:
    def __init__(self, suite, face):
        self.suite = suite
        self.face = face

    def point(self):
        if self.face <= 10:
            return self.face
        else:
            return 10

    def __str__(self):
        if self.face == 11:
            self_str = 'J'
        elif self.face == 12:
            self_str = 'Q'
        elif self.face == 13:
            self_str = 'K'
        elif self.face == 1:
            self_str = 'A'
        else:
            self_str = str(self.face)
        return '%s%s' % (self.suite, self_str)

    def __repr__(self):
        return self.__str__()

class Joker:
    def __init__(self, current = 0):
        self.cards = [Card(suite, face) for suite in '♦♥♠♣' for face in range(1,14)]*4
        self.current = current

    def shuffle(self):
        """Shuffle the deck of cards."""
        return random.shuffle(self.cards)

    def next(self, new_round = False): 
        """Get the next card from the deck."""
        if new_round:
            self.shuffle()
            self.current = 0
        else:
            card = self.cards[self.current]
            self.current += 1
            return card

    def has_next_card(self):
        """Check if there is any card left in the deck."""
        if self.current != len(self.cards):
            return True
        else:
            return False

class Player:
    """
    Represents a player in a blackjack game.
    Attributes:
        name (str): The name of the player.
        money (float): The amount of money the player has.
        cards_on_hand (list): The list of cards the player has in hand.
    Methods:
        hit(card): Adds a card to the player's hand.
        sort_cards(card_keys): Sorts the player's cards based on the given keys.
        first_2_sum_point(): Calculates the sum of the first two cards' points.
        current_point(): Calculates the current total points of the player's cards.
        show(score): Displays the player's name, cards in hand, and score.
    """
    def __init__(self, name, money):
        self.name = name
        self.money = money
        self.cards_on_hand = []

    def hit(self, card):
        """add a card to the player's hand."""
        self.cards_on_hand.append(card)

    def sort_cards(self, card_keys):
        """sort the player's cards based on the given keys."""
        self.cards_on_hand.sort(key = card_keys)

    def first_2_sum_point(self):
        """
        Calculates the sum of the points of the first two cards in the player's hand.
        Returns:
            int: The sum of the points of the first two cards.
        """
        special_card = [1 for card in self.cards_on_hand[:2] if card.face == 1]
        sum_point = np.cumsum([card.point() for card in self.cards_on_hand[:2]])[-1]
        if special_card == [1] and sum_point <= 11:
            sum_point += 10
        elif special_card == [1,1]:
            sum_point = 12
        return sum_point

    def current_point(self):
        """
        Calculates the current total points of the player's cards.
        Returns:
            int: The current total points of the player's cards.
        """
        current_point = self.first_2_sum_point()
        current_card_counts = len(self.cards_on_hand)
        special_card = [1 for card in self.cards_on_hand[:2] if card.face == 1]
        if special_card == []:
            current_ace_count = 0
        else:
            current_ace_count = np.cumsum(special_card)[0]
        for i in range(2,current_card_counts):
            if current_point >= 4 and current_point <= 10:
                if self.cards_on_hand[i].face == 1:
                    current_ace_count += 1
                    current_point += 11
                else:
                    current_point += self.cards_on_hand[i].point()

            elif current_point > 10 and current_point <= 16:
                current_point += self.cards_on_hand[i].point()
                if current_point > 21 and current_ace_count > 0:
                    current_point -= 10
                    current_ace_count -= 1
        return current_point

    def show(self, score):
        """
        Displays the player's name, cards in hand, and score.
        Parameters:
            score (int): The score of the player's cards.
        """
        print('%s got %s in its hand.' %
              (self.name, self.cards_on_hand))
        print("%s's cards have score %d" % (self.name, score))


class Dealer(Player):
    def __init__(self, name):
        super().__init__(name, float('inf'))

    def dealer_final_point(self, joker):
        """calculate the dealer's final points."""
        dealer_current_point = self.first_2_sum_point()
        while dealer_current_point < 17:
            self.hit(joker.next())
            dealer_current_point = self.current_point()
        return dealer_current_point


class Gumbler(Player):
    def __init__(self, name, money):
        Player.__init__(self, name, money)

    def gambler_final_point(self, dealer, joker):
        """calculate the gambler's final points."""
        if dealer.cards_on_hand[0].face >= 2 and dealer.cards_on_hand[0].face <= 6:
            gambler_current_point = self.first_2_sum_point()
            while gambler_current_point < 12:
                self.hit(joker.next())
                gambler_current_point = self.current_point()
            return gambler_current_point
        else:
            gambler_current_point = self.first_2_sum_point()
            while gambler_current_point < 17:
                self.hit(joker.next())
                gambler_current_point = self.current_point()
            return gambler_current_point
        # return self.current_point()

def get_key(card):
    """Get the key of the card."""
    return card.face

# ===== Just play one round of the game =====
# play_automaticly
def play_one_round_auto(player_money = 500, bet = 10):
    """Automatically/user manually play one round of the game and display the result."""
    poke = Joker()
    dealer = Dealer('Dealer')
    p1 = Gumbler('Player', player_money)
    poke.shuffle()
    for i in range(1,3):
        p1.hit(poke.next())
        dealer.hit(poke.next())
    dealer.sort_cards(get_key)
    p1.sort_cards(get_key)
    # if mode == 0:
    #     p1.show(p1.first_2_sum_point())
    #     dealer.show(dealer.first_2_sum_point())
    dealer_score = dealer.dealer_final_point(poke)
    gambler_score = p1.gambler_final_point(dealer, poke)
    poke.shuffle()
    return dealer, p1, dealer_score, gambler_score, bet


def play_one_round_manu(hit_button=0, player_money=500, bet=10):
    """Automatically/user manually play one round of the game and display the result."""
    if 'poke' not in st.session_state:
        st.session_state.poke = Joker()
        st.session_state.dealer = Dealer('Dealer')
        st.session_state.p1 = Gumbler('Player', player_money)
        st.session_state.poke.shuffle()

        for i in range(1, 3):
            st.session_state.p1.hit(st.session_state.poke.next())
            st.session_state.dealer.hit(st.session_state.poke.next())
        st.session_state.dealer.sort_cards(get_key)
        st.session_state.p1.sort_cards(get_key)
        dealer_score = st.session_state.dealer.dealer_final_point(st.session_state.poke)
    else:
        if hit_button:
            st.session_state.p1.hit(st.session_state.poke.next())

    dealer_score = st.session_state.dealer.current_point()
    gambler_score = st.session_state.p1.current_point()
    return st.session_state.dealer, st.session_state.p1, dealer_score, gambler_score, bet


def result_msg(dealer, p1, gambler_score, dealer_score, bet):
    """Present the final result of the game."""
    print("======Final Result======")
    msg_win = "Nice game, you win!"
    msg_lose = "Sorry, dealer wins."
    msg_equal = "Equal Game,Play again"
    bet_win = f"You win ${bet}"
    bet_lose = f"You lose ${bet}"
    bet_equal = "No money win or lose."
    if gambler_score > 21:
        # print('Sorry, dealer wins.')
        # print(f"You lose ${bet}")
        return msg_lose, bet_lose, dealer.cards_on_hand, p1.cards_on_hand
    elif dealer_score >21:
        # print('Nice game, you win!')
        # print(f"You win ${bet}")
        return msg_win, bet_win, dealer.cards_on_hand, p1.cards_on_hand
    elif gambler_score == 21 and dealer_score == 21:
        if len(dealer.cards_on_hand) == 2 and len(p1.cards_on_hand) > 2:
            # print('Sorry, dealer wins.')
            # print(f"You lose ${bet}")
            return msg_lose, bet_lose, dealer.cards_on_hand, p1.cards_on_hand
        elif len(p1.cards_on_hand) == 2 and len(dealer.cards_on_hand) > 2:
            # print('Nice game, you win!')
            # print(f"You win ${bet * 1.5}")
            return msg_win, bet_win, dealer.cards_on_hand, p1.cards_on_hand
        else:
            return msg_equal, bet_equal, dealer.cards_on_hand, p1.cards_on_hand
    elif dealer_score > gambler_score:
        # print('Sorry, dealer wins.')
        # print(f"You lose ${bet}")
        return msg_lose, bet_lose, dealer.cards_on_hand, p1.cards_on_hand
    elif dealer_score == gambler_score:
        # print('Equal Game,Play again')
        return msg_equal, bet_equal, dealer.cards_on_hand, p1.cards_on_hand
    else:
        # print('Nice game, you win!')
        # print(f"You win ${bet}")
        return msg_win, bet_win, dealer.cards_on_hand, p1.cards_on_hand



# ===== The following is related to the statistic report =====
def play_one_round_return_winner(poke, dealer, p1):
    """Play one round and return the winner of the round."""
    for i in range(1,3):
        p1.hit(poke.next())
        dealer.hit(poke.next())
    dealer.sort_cards(get_key)
    p1.sort_cards(get_key)
    dealer_score = dealer.dealer_final_point(poke)
    gambler_score = p1.gambler_final_point(dealer, poke)
    if gambler_score > 21:
        return 'dealer'
    elif dealer_score >21:
        return 'gambler'
    elif gambler_score == 21 and dealer_score == 21:
        if len(dealer.cards_on_hand) == 2 and len(p1.cards_on_hand) > 2:
            return 'dealer'
        elif len(p1.cards_on_hand) == 2 and len(dealer.cards_on_hand) > 2:
            return 'gambler'
        else:
            return 'Equal'
    elif dealer_score > gambler_score:
        return 'dealer'
    elif dealer_score == gambler_score:
        return 'Equal'
    else:
        return 'gambler'


def calculate_winner_of_rounds(player_money=500):
    """Calculate the winner of n rounds of the game."""
    poke = Joker()
    dealer = Dealer('dealer')
    p1 = Gumbler('gambler', player_money)
    poke.shuffle()
    winner_record = play_one_round_return_winner(poke, dealer, p1)
    return winner_record

def generate_strategy_report(n):
    """Generate a strategy dataframe report for n rounds of the game about winner and win rate."""
    winner_record_list = []
    for group in range(1,n+1):
        winner_record_list.append(calculate_winner_of_rounds())
    round_index = list(range(1, n+1))
    player_if_win = [1 if winner == 'gambler' else 0 for winner in winner_record_list]
    dealer_if_win = [1 if winner == 'dealer' else 0 for winner in winner_record_list]
    if_draw = [1 if winner == 'Equal' else 0 for winner in winner_record_list]
    player_total_win = np.cumsum(player_if_win)
    dealer_total_win = np.cumsum(dealer_if_win)
    draw_total = np.cumsum(if_draw)
    player_total_win_rate = player_total_win / round_index
    dealer_total_win_rate = dealer_total_win / round_index
    draw_total_rate = draw_total / round_index
    
    report_df = pd.DataFrame({
        'round_index': round_index,
        'player_if_win': player_if_win,
        'dealer_if_win': dealer_if_win,
        'if_draw': if_draw,
        'player_total_win': player_total_win,
        'dealer_total_win': dealer_total_win,
        'draw_total': draw_total,
        'player_total_win_rate': player_total_win_rate,
        'dealer_total_win_rate': dealer_total_win_rate,
        'draw_total_rate': draw_total_rate
    })
    
    return report_df, player_total_win_rate[-1]

def plot_total_winning_rate(report_df):
    """
    Plot the strategy report with the player and dealer win rates.
    """
    fig1 = plt.figure(figsize=(10, 6))
    ax = plt.axes()
    ax.plot(report_df['round_index'], report_df['player_total_win_rate'], label='Player Win Rate')
    ax.plot(report_df['round_index'], report_df['dealer_total_win_rate'], label='Dealer Win Rate')
    ax.set_xlabel('Number of Rounds')
    ax.set_ylabel('Win Rate')
    xtick = np.arange(0, report_df['round_index'].max()+1, 50)
    ax.set_xticks(xtick)
    ax.set_xticklabels(xtick)
    ax.set_title('Strategy Report')
    ax.legend()
    ax.grid(True)
    return fig1
    # plt.show()


def plot_binomial_distribution(n, p, win_number):
    """
    Plot Luck distribution graph for the player.
    Parameters:
        n (int): The number of total rounds player choose.
        p (float): The player's winning rate from 10000 rounds simulation used as the winning possibility of player.
        win_number (int): The number of rounds player win within the chosen rounds.
    """
    # Parameters for the binomial distribution
    N = n    
    p = p  
    x = np.arange(0, N+1)
    # Calculate the binomial probability mass function (PMF)
    binom_pmf = binom.pmf(x, N, p)
    x_line = win_number
    area_left = binom.cdf(x_line, N, p)

    # Create the plot with ax style
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.plot(x, binom_pmf, label=f'Binomial PMF (N={N}, p={p})', color='blue')

    # Add a vertical line at x = win_number
    ax.axvline(x=x_line, color='r', linestyle='--', label=f'x = {x_line}')
    ax.fill_between(x[:x_line+1], binom_pmf[:x_line+1], color='blue', alpha=0.3)

    # Annotate the area on the left of the line
    ax.text(x_line, max(binom_pmf)/2, f'Area left of {x_line} = {area_left:.4f}', color='red')

    # Add titles and labels
    ax.set_title(f'Your Luck Today: Beating {area_left*100:.2f}% of the players')
    ax.set_xlabel('Number of successes')
    ax.set_ylabel('Probability')
    ax.legend()
    ax.grid(True)
    
    return fig, area_left


# ===== The following is related to streamlit web page =====
# create a function to set the style of the page
st.markdown("""
        <style>
        .main-title {
            font-size: 32px;
            font-weight: bold;
            color: #8B4513;
            text-align: center;
            font-family: 'Courier New', Courier, monospace;
        }
        .sub-title {
            font-size: 24px;
            font-weight: bold;
            color: #A0522D;
            margin-top: 20px;
            font-family: 'Courier New', Courier, monospace;
        }
        .content-block {
            background-color: #FFF8DC;
            color: #000000;
            padding: 20px;
            margin: 20px 0;
            border-radius: 10px;
            box-shadow: 2px 2px 5px #A0522D;
            font-family: 'Courier New', Courier, monospace;
        }
        .banner-image {
            display: block;
            margin-left: auto;
            margin-right: auto;
            width: 100%;
        }
        .text {
            font-family: 'Courier New', Courier, monospace;
            font-size: 18px;
        }
        </style>
    """, unsafe_allow_html=True)

def main():
    """Main function to run the blackjack game in streamlit."""
    # Create navigation
    page = st.sidebar.selectbox("Select Page", ["Home", "PlayGround with Statistics"])

    if page == "Home":
        show_home_page()
    elif page == "PlayGround with Statistics":
        show_statistics_page()

def show_home_page():
    """Show the home page of the blackjack game in streamlit."""
    # st.markdown("<div class='main-title'>♠♥Blackjack Playground♦♣</div>", unsafe_allow_html=True)
    
    # Banner Image using a local file path
    st.markdown(f"""
        <div style='text-align: center;'>
            <img src='https://www.treasurybrisbane.com.au/sites/treasurybrisbane.com.au/files/styles/max_carousel/public/thumbnails/image/TableGames_Blackjack_Banner.jpg?itok=z1VBFK2h' class='banner-image' alt='Blackjack Playground'>
        </div>
    """, unsafe_allow_html=True)
    
    # Introduction Block
    st.markdown("<div class='sub-title'>Introduction</div>", unsafe_allow_html=True)
    st.markdown("""
        <div class='content-block text'>
            Blackjack, also known as 21, is a popular casino card game. The objective is to beat the dealer by having a hand value 
            as close to 21 as possible without exceeding it. Face cards are worth 10 points, Aces can be worth 1 or 11 points, 
            and all other cards are worth their face value.
        </div>
    """, unsafe_allow_html=True)
    
    # How to Play Block
    st.markdown("<div class='sub-title'>How to Play</div>", unsafe_allow_html=True)
    st.markdown("""
        <div class='content-block text'>
            <ol>
                <li>Place your bet.</li>
                <li>Receive two cards, while the dealer gets one card face up and one card face down.</li>
                <li>Decide whether to "Hit" (take another card) or "Stand" (keep your current hand).</li>
                <li>If your hand exceeds 21, you bust and lose the bet.</li>
                <li>Once you stand, the dealer reveals the face-down card and draws until reaching 17 or higher.</li>
                <li>The closest hand to 21 wins. If tied, it’s a draw.</li>
            </ol>
        </div>
    """, unsafe_allow_html=True)
    
    # Simple Strategy Checksheet Block
    # Apply the color function to the dataframe
    filename = 'cheetsheet.txt'
    styled_df = get_cheetsheet(filename).style.applymap(color_cells)
    st.markdown("<div class='sub-title'>Blackjack Simple Strategy Checksheet</div>", unsafe_allow_html=True)
    st.markdown("""
        <div class='content-block text'>
            This table shows a simple strategy for playing blackjack based on the dealer's upcard.
        </div>
    """, unsafe_allow_html=True)
    st.table(styled_df)
    st.markdown("***Note: S = Stand, H = Hit, D = Double Down (here we make it as Hit)***")

    # Autoplay Ground Block
    st.markdown("<div class='sub-title'>Autoplay Ground</div>", unsafe_allow_html=True)
    st.markdown("""
        <div class='content-block text'>
                Still feeling hard to remember the strategy?
                Let's make it super easy for you! Just click autoplay button to play!
        </div>
    """, unsafe_allow_html=True)

    autoplay_play()

    # Play by Yourself Block
    st.markdown("<div class='sub-title'>Play by Yourself</div>", unsafe_allow_html=True)
    st.markdown("""
        <div class='content-block text'>
                Confident in your blackjack skills? Play by yourself and see how you do! Hit Start to begin for each round.
        </div>
    """, unsafe_allow_html=True)

    manual_play()

def show_statistics_page():
    """Show the page of Statistics Ground"""
    st.markdown(f"""
        <div style='text-align: center;'>
            <img src='https://www.treasurybrisbane.com.au/sites/treasurybrisbane.com.au/files/styles/max_carousel/public/thumbnails/image/TableGames_Blackjack_Banner.jpg?itok=z1VBFK2h' class='banner-image' alt='Blackjack Playground'>
        </div>
    """, unsafe_allow_html=True)
    st.markdown("<div class='sub-title'>Statistics Ground</div>", unsafe_allow_html=True)
    st.markdown("""
        <div class='content-block text'>
                Let's see how lucky you are today? 
        </div>
    """, unsafe_allow_html=True)
    option = st.selectbox(
        "Play for how many rounds?",
        ("50","75" ,"100"))
    st.write("You selected:", option)
    n = int(option)
    if st.button("Show Statistics"):
        show_statistics(n)

def read_file(filename):
    """Read file to create a dataframe for the strategy checksheet"""
    infile = open(filename, 'r')
    lines = infile.readlines()
    infile.close()
    data = []
    for line in lines[1:12]:
        data.append(line.strip().split(','))
    df = pd.DataFrame(data[1:], columns=data[0])
    return df

def get_cheetsheet(filename):
    """Get the strategy checksheet when the file couldn't be read"""
    try:
        df = read_file(filename)
    except FileNotFoundError:
        data_backup = {
            "Dealer Upcard": ["2", "3", "4", "5", "6", "7", "8", "9", "10", "A"],
            "17": ["S", "S", "S", "S", "S", "S", "S", "S", "S", "S"],
            "16": ["S", "S", "S", "S", "S", "H", "H", "H", "H", "H"],
            "15": ["S", "S", "S", "S", "S", "H", "H", "H", "H", "H"],
            "14": ["S", "S", "S", "S", "S", "H", "H", "H", "H", "H"],
            "13": ["S", "S", "S", "S", "S", "H", "H", "H", "H", "H"],
            "12": ["H", "H", "S", "S", "S", "H", "H", "H", "H", "H"],
            "11": ["D", "D", "D", "D", "D", "D", "D", "D", "D", "D"],
            "10": ["D", "D", "D", "D", "D", "D", "D", "D", "H", "H"],
            "9": ["H", "D", "D", "D", "D", "H", "H", "H", "H", "H"],
            "8": ["H", "H", "H", "H", "H", "H", "H", "H", "H", "H"]
        }
        df = pd.DataFrame(data_backup)
    return df

def color_cells(val):
    """Apply color to the cells based on the value"""
    color = ''
    if val == 'S':
        color = 'background-color: lightgreen; color: black'
    elif val == 'H':
        color = 'background-color: lightcoral; color: black'
    elif val == 'D':
        color = 'background-color: lightblue; color: black'
    return color

def autoplay_play():
    """This is the autoplay function for the AutoPlay block."""
    bet = st.number_input("Enter your bet $", min_value=10)
    if st.button("Start Autoplay"):
        dealer, p1, dealer_score, gambler_score, bet = play_one_round_auto(player_money=500, bet=bet)
        msg, bet_msg, dealer_cards, p1_cards = result_msg(dealer, p1, gambler_score, dealer_score, bet)
        st.markdown(f"""
            <div class='content-block text'>
                <p>Dealer's cards: {dealer_cards}. Dealer's final number: {dealer_score}</p>
                <p>Your cards: {p1_cards}. Your final number: {gambler_score}</p>
                <p>=====Final Result=====</p>
                <p>{msg}</p>
                <p>{bet_msg}</p>
            </div>
        """, unsafe_allow_html=True)

def manual_play():
    """This is the designed function for Play by yourself block where the user to play manually about hit and stand."""
    bet = st.number_input("Enter your bet", min_value=10, key='bet_input')
    start_button = st.button("Start")

    if start_button:
        # Resetting the game state when the start button is pressed
        st.session_state['game_started'] = True
        st.session_state.pop('poke', None)  # Remove the deck from the session if it exists
        st.session_state.pop('hit', None)   # Remove any existing hit state
        st.session_state.pop('stand', None) # Remove any existing stand state

    if 'game_started' in st.session_state and st.session_state['game_started']:
        dealer, p1, dealer_score, gambler_score, bet = play_one_round_manu(hit_button=0, player_money=500, bet=bet)
        msg, bet_msg, dealer_cards, p1_cards = result_msg(dealer, p1, gambler_score, dealer_score, bet)
        st.markdown(f"""
        <div class='content-block text'>
            <p>Dealer's first card: {dealer_cards[0]}</p>
            <p>Your cards: {p1_cards}. Your final number: {gambler_score}</p>
        </div>
        """, unsafe_allow_html=True)
        hit_button = st.button("Hit (One More Card)")
        stand_button = st.button("Stand (Show Result)")

        if hit_button:
            dealer, p1, dealer_score, gambler_score, bet = play_one_round_manu(hit_button=1, player_money=500, bet=bet)
            msg, bet_msg, dealer_cards, p1_cards = result_msg(dealer, p1, gambler_score, dealer_score, bet)
            st.markdown(f"""
            <div class='content-block text'>
                <p>Dealer's first card: {dealer_cards[0]}</p>
                <p>Your cards: {p1_cards}. Your total number: {gambler_score}</p>
            </div>
            """, unsafe_allow_html=True)
            # st.write(f"Dealer's first card: {dealer_cards[0]}")
            # st.write(f"Player's cards: {p1_cards}. Your total number: {gambler_score}")
            if gambler_score > 21:
                st.markdown(f"""
                <div class='content-block text'>
                    <p>You bust!</p>
                    <p>Hit Start to play again</p>
                </div>
                """, unsafe_allow_html=True)
                # st.write("You bust!")
                st.session_state['game_started'] = False  # Reset game state

        if stand_button:
            # Directly display the results without adding more cards
            st.markdown(f"""
            <div class='content-block text'>
                <p>Dealer's cards: {dealer_cards}. Dealer's final number: {dealer_score}</p>
                <p>Your cards: {p1_cards}. Your final number: {gambler_score}</p>
                <p>=====Final Result=====</p>
                <p>{msg}</p>
                <p>{bet_msg}</p>
            </div>
            """, unsafe_allow_html=True)
            st.session_state['game_started'] = False  # Reset game state


def show_statistics(n):
    """This is the function for the Statistics Ground block which shows the statistics graph of the game."""
    st.markdown("<div class='content-block text'>Statistics Board</div>", unsafe_allow_html=True)
    report_df, _ = generate_strategy_report(n)
    _, player_winning_rate = generate_strategy_report(10000)
    col1, col2, col3 = st.columns(3)
    win_loss_draw_list = list(report_df.iloc[-1, -3:])
    col2.metric("Player winning Rate", f"{win_loss_draw_list[0]*100:.1f}%")
    col1.metric("Dealer winning Rate", f"{win_loss_draw_list[1]*100:.1f}%")
    col3.metric("Draw Rate", f"{win_loss_draw_list[2]*100:.1f}%")

    st.markdown(":blue-background[**Total Winning Rate Graph**]")
    report_df_copy = report_df.copy().rename(columns={"player_total_win_rate": "Player", "dealer_total_win_rate": "Dealer", "draw_total_rate": "Equal", "round_index": "Round"})
    st.line_chart(report_df_copy, x="Round", y=["Player", "Dealer", "Equal"])
    # fig1 = plot_total_winning_rate(report_df)
    # st.pyplot(fig1)

    win_number = int(n * win_loss_draw_list[0])
    fig2, area_left = plot_binomial_distribution(n, player_winning_rate, win_number)
    st.markdown(":blue-background[**Your Luck Distribution Graph**]")
    st.pyplot(fig2)
    st.markdown("***Note: The absolute winning rate of player is calculated in 10000 rounds simulation.***")

if __name__ == "__main__":
    main()
