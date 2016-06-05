#Decides booze spending
expenditure_total = raw_input('expenditure')
favorite = raw_input('Favorites')
how_many = raw_input('How many people want weed')
suggestion =[]
def select_booze(expenditure,favorites,how_many_weed):
    suggestion = []
    if how_many_weed > 2:
        #No need for weed for less than two people. spending 500 seems obscene if its two or less. Adds to suggesion that weed should be there
        suggestion.append('Weed should be there')
    else:
        suggestion.append('Weed shouldnt be there as there are not enough people that want it')

    if 'Old No.7' or 'Tenesse Honey' or 'Gentleman Jack' in favorites and expenditure < 4500:
        suggestion.append('Sorry no Jack for you')
    elif 'Gentleman Jack' in favorites and expenditure > 4500:
        suggestion.append('You can get Gentleman Jack')
    elif 'Tenesse Honey' in favorites and expenditure > 4000:
        suggestion.append('You can get Tenesse Honey')
    elif 'Old No.7' in favorites and expenditure > 3500:
        suggestion.append('You can get Old No.7, if so, remaining balance:')
    elif 'Jim Beam' in favorites and expenditure >1200:
        suggestion.append('You can get all types of Jim Beam!')

    return suggestion


select_booze(expenditure=expenditure_total,favorites=favorite,how_many_weed=how_many)