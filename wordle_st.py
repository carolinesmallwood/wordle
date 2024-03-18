import streamlit as st
import pandas as pd
import numpy as np
from collections import Counter

def main():
    
    ## CUSTOMIZE THESE
    # max number of attempts
    attempt_limit = 6

    # location of raw word list file
    path_to_dict = "2of12id.txt"

    # location of cleaned word list with Used flag set from previous games
    path_to_df = ''
    
        # formatting codes
    black = '\033[30m'
    grey = '\033[90m'
    green = '\033[32m'
    yellow = '\033[93m'
    
    
    d = st.text_input('Enter R to reset dictionary, U to avoid used words')
    if d == 'U':
        load_word_list(path_to_df, True)
    else:
        load_word_list(path_to_dict, False)
        
    still_playing = True
    while (still_playing):
        play()
        
        p = st.text_input('Hit enter to play again. Enter X to quit!')
        if p == 'X':
            still_playing = False
            st.write('Thanks for playing!')


def load_word_list(dict_file, log):
    """ Loads list of candidate target words, cleans, adds columns
    
    Args:
        dict_file (str): path to word list file
        log (bool): indicates whether this is raw file or previously used word_list with Used flag
        
    Returns:
        df: dataframe of words and attributes
    """
    
    # if this is a logged word_list, we can just load and return 
    if log:
        words = pd.read_csv(dict_file)
        return words
    
    word_list = []
    with open (dict_file) as f:
        s = f.readLine()
        while (s):
            s_list = s.split()
            if s_list[0][0].isalpha():
                word_list.append(s_list[0])
            s = f.readLine()

    words = pd.DataFrame(word_list).drop_duplicates()
    words.columns = ['word']
    
    words = pd.DataFrame(word_list).drop_duplicates()
    words.columns = ['word']
    
    
    # format to uppercase
    words['word'] = words['word'].apply(str.upper)
    #  create length column
    words['length'] = words['word'].apply(len)
    # add flag to indicate if word has been used
    words['used'] = False
    
    # sort word list by length
    words = words.sort_values('length').reset_index(drop=True)

    words = words.reset_index()

    # cast word as str instead of object
    words['word'] = words['word'].astype('str')
        
    
## How would performance change if we filtered word_list down to l-length words and then passed to function?
def pick_random_word(l, word_list):
    """ Returns target word
    
    Args:
        l (int): length of target word
        word_list (df): list of words, cols = ['word', 'length', 'used']
    
    Returns:
        str: target word of length l which hasn't been used before
    
    """
    
    # get index of first word of that length
    beg = word_list[word_list.length == l]['index'].idxmin()
    end = word_list[word_list.length == l]['index'].idxmax() + 1
    
    index = random.randint(beg, end)
    
    # check if word has been used
    # reassign if True
    while (word_list.iloc[index].used):
        index = random.randint(beg, end)
    
    # set used flag to True
    word_list.iloc[index, 3] = True
    
    return word_list.iloc[index]['word']


def get_attempt(l, word_list):
    """ Gets word guess from input
    
    get_attempt checks both that input is correct length l and that input is in word_list
    If not, requests more input until true.
    
    Args:
        l (int): length of target word
        word_list (df): list of words, cols = ['word', 'length', 'used']
        
    Returns:
        str: validated word guess
    
    """
    
    guess = st.text_input('Guess a ' + str(l) + '-character word:')
    
    if len(guess) != l:
        return -1
    
    while (guess.upper() not in word_list['word'].values):
        guess = st.text_input("That word isn't in our dictionary. Try again:")
        
    return guess


def evaluate_attempt(guess, word, alphabet):
    """ Evaluates word guess and returns color codes and remaining alphabet
    
    Args:
        guess (str): guess of the target word
        word (str): target word
        alphabet (list): list of remaining possible letters (as chars)
        
    Returns:
        list of chars: one char per letter of target word/guess, corresponding to the color code
        for that guessed letter
        
        list of chars: remaining possible letters
    
    """
    
    # set guess_colors to black by default
    guess_colors = ['k'] * len(word)
    count = Counter(word)
    
    # first pass: determine green letters
    for i in range(0, len(word)):
        if guess[i] == word[i]:
            # if letter is correct, label it green
            guess_colors[i] = 'g'
            # decrement number of that letter remaining
            count[word[i]] -= 1
        elif guess[i] in count:
            # if letter is in word, but wrong spot
            if count[guess[i]] > 0:
                # if we haven't already put green/yellow labels equal to num of that letter
                # label yellow
                guess_colors[i] = 'y'
                count[guess[i]] -= 1
        else:
            # if letter is not in word, remove it from working alphabet
            if guess[i] in alphabet:
                alphabet.remove(guess[i])
    
    return guess_colors, alphabet
                

def display_attempts(guess_array, color_array, a, l):
    """ Constructs color-coded string summary of all guesses
    
    Args:
        guess_array (np ndarray):  ndarray with shape (a, l) of all guesses
        color_array (np ndarray):  ndarray with shape (1, l) of guess color codes
        a (int):                   number of guesses
        l (int):                   length of target word
    
    """
    
    disp = ""
    # iterate over guesses
    for i in range(a+1):
        # iterate over letters in guess
        for j in range(l):
            if color_array[i,j] == 'y':
                disp += " " + yellow + guess_array[i,j] 
            elif color_array[i,j] == 'g':
                disp += " " + green + guess_array[i,j]
            else:
                disp += " " + black + guess_array[i,j]
        
        disp += "\n"
    
    return disp


def play():
    """ Executes one round of wordle
    
    """
    
    l = st.text_input('Choose Wordle length between 5 and 10:')
    
    if int(l) not in range(5, 11):
        l = st.text_input('Length must be integer between 5 and 10. Try again:')
    
    if int(l) not in range(5, 11):
        st.write("Two strikes and you're out. Must rerun game.")
        return
    
    target_len = int(l)
    
    target = pick_random_word(target_len)
    
    target_arr = np.array(list(target.upper()))
    
    attempt = 0
    guesses = np.empty([attempt_limit, len(target)], dtype=str)
    colors = np.empty([attempt_limit, len(target)], dtype=str)
    alphabet = list(map(chr, range(65, 91)))
    
    while (attempt < attempt_limit):
        
        g = get_attempt(target_len)
        
        if g == -1:
            st.write("You can't follow directions!")
            return
        
        g = g.upper()
        
        c, alphabet = evaluate_attempt(g.upper(), target, alphabet)
        
        guesses[attempt] = list(g)
        colors[attempt] = c
        
        st.write(display_attempts(guesses, colors, attempt, target_len))
        
        if g.upper() == target:
            st.write(black + 'Congratulations! The wordle was ' + target + '!')
            return
        
        alph = black + ''
        for char in alphabet:
            alph += " " + char
        st.write(alph)
        
        attempt += 1
        
    st.write(black + 'Better luck next time, the wordle was ' + target + '!')

if __name__ == '__main__':
    main()



    

    
    
    
    
    