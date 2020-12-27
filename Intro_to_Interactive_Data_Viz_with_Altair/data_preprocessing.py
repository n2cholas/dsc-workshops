import pandas as pd

df = pd.read_csv(
    'https://raw.githubusercontent.com/n2cholas/pokemon-analysis/master/pokemon-data.csv',
    delimiter=';')
mdf = pd.read_csv(
    'https://raw.githubusercontent.com/n2cholas/pokemon-analysis/master/move-data.csv',
    delimiter=';')

print('Number of pokemon: ', len(df))

mdf.columns = [
    'index', 'name', 'type', 'category', 'contest', 'pp', 'power', 'accuracy',
    'generation'
]
mdf['power'].replace('None', 0, inplace=True)
mdf['accuracy'].replace('None', 100, inplace=True)
mdf['power'] = pd.to_numeric(mdf['power'])
mdf['accuracy'] = pd.to_numeric(mdf['accuracy'])

df.columns = [
    'name', 'types', 'abilities', 'tier', 'hp', 'atk', 'def', 'spa', 'spd',
    'spe', 'next_evos', 'moves'
]

# turn list strings into actual lists
df['next_evos'] = df.next_evos.map(eval)
df['types'] = df.types.map(eval)
df['abilities'] = df.abilities.map(eval)
df['moves'] = df.moves.map(eval)

df.set_index('name', inplace=True)

weird_moves = set()

for ind, row in df.iterrows():
    for move in row.moves:
        if "'" in move:
            weird_moves.add(move)

print('Weird Moves: ', weird_moves)

weird_moves.remove("King's Shield")
weird_moves.remove("Forest's Curse")
weird_moves.remove("Land's Wrath")
weird_moves.remove("Nature's Madness")

df['moves'] = df.apply(lambda x: [
    move if move not in weird_moves else move.replace("'", "-")
    for move in x.moves
],
                       axis=1)

removal_check_set = set()
for ind, row in df.iterrows():
    for move in row.moves:
        if "'" in move:
            removal_check_set.add(move)

print('Weird Moves After Removal', removal_check_set)

df['moves'] = df.moves.map(set)

mdf = mdf[(mdf.pp != 1) | (mdf.name == 'Struggle')]  # remove invalid moves

df.loc['Victini', 'moves'].add('V-create')
df.loc['Rayquaza', 'moves'].add(
    'V-create')  #technically should have Mega Rayquaza as well, but it's in AG
df.loc['Celebi', 'moves'].add('Hold Back')

for pok in ['Zygarde', 'Zygarde-10%', 'Zygarde-Complete']:
    df.loc[pok, 'moves'].add('Thousand Arrows')
    df.loc[pok, 'moves'].add('Thousand Waves')
    df.loc[pok, 'moves'].add('Core Enforcer')

for pok in ['Celebi', 'Serperior', 'Emboar',
            'Samurott']:  #'Mareep', 'Beldum', 'Munchlax' are all LC
    df.loc[pok, 'moves'].add('Hold Back')

mdf = mdf[(mdf.name != 'Happy Hour') & (mdf.name != 'Celebrate') &
          (mdf.name != 'Hold Hands') & (mdf.name != 'Plasma Fists')]


def stage_in_evo(n):
    # returns number of evolutions before it
    bool_arr = df.apply(lambda x: n in x['next_evos'] and
                        (n + '-') not in x['next_evos'],
                        axis=1)  #gets index of previous evolution
    if ('-' in n and n.split('-')[0] in df.index and
            n != 'Porygon-Z'):  #'-Mega' in n or
        #megas and alternate forms should have same evolutionary stage as their base
        return stage_in_evo(n.split('-')[0])
    elif not any(bool_arr):
        return 1  # if there's nothing before it, it's the first
    else:
        return 1 + stage_in_evo(df.index[bool_arr][0])


def num_evos(n):
    if n not in df.index:  #checks to ensure valid pokemon
        return n

    next_evos = df.loc[n, 'next_evos']
    if len(next_evos) > 0:  # existence of next_evo
        if n in next_evos[0]:  # if "next evo" is an alternate form
            return df.loc[n, 'stage']  #accounting for alternate forms
        else:
            return num_evos(next_evos[0])
    elif '-Mega' in n or (n.split('-')[0] in df.index and n != 'Porygon-Z'):
        # this is checking if there is a pokemon with the same root name
        # (e.g. Shaymin vs Shaymin-Sky)
        return df.loc[n.split('-')[0], 'stage']
    else:
        return df.loc[n, 'stage']


df['stage'] = df.index.map(stage_in_evo)
df['num_evos'] = df.index.map(num_evos)
df['evo_progress'] = df['stage'] / df['num_evos']

df['mega'] = df.index.map(lambda x: 1 if '-Mega' in x else 0)
df['alt_form'] = df.apply(
    lambda x: 1
    if ('-' in x.name and x.mega == 0 and '-Alola' not in x.name and x.name.
        split('-')[0] in df.index and x.name != 'Porygon-Z') else 0,
    axis=1)

df.loc[df.tier.isna(), 'tier'] = 'No Tier'
df['num_moves'] = df.moves.map(len)
df['bst'] = df['hp'] + df['atk'] + df['def'] + df['spa'] + df['spd'] + df['spe']
mdf.loc[mdf.name == 'Frusuration', 'power'] = 102
mdf.loc[mdf.name == 'Return', 'power'] = 102

bad_abilities = {
    'Comatose', 'Defeatist', 'Emergency Exit', 'Slow Start', 'Truant',
    'Wimp Out', 'Stall'
}
df['bad_ability'] = df.abilities.map(
    lambda x: all(map(lambda y: y in bad_abilities, x))).astype(int)

df['type1'] = df.types.map(lambda x: x[0])
df['type2'] = df.types.map(lambda x: x[1] if len(x) == 2 else '')

df['num_types'] = df.types.map(len)
df['num_abilities'] = df.abilities.map(len)

df = df.reset_index()

df['ability1'] = df.abilities.map(lambda x: x[0])
df['ability2'] = df.abilities.map(lambda x: x[1] if len(x) > 1 else '')
df['ability3'] = df.abilities.map(lambda x: x[2] if len(x) > 2 else '')

# Split Basculin Red/Blue into 2 pokemon (because diff abilities)
df = df.append(df[df.name == 'Basculin'])
df.iloc[38, 0] = 'Basculin-Red'
df.iloc[-1, 0] = 'Basculin-Blue'
df.loc[df.name == 'Basculin-Red', 'ability1'] = 'Reckless'
df.loc[df.name == 'Basculin-Red', 'ability2'] = 'Adaptability'
df.loc[df.name == 'Basculin-Red', 'ability3'] = 'Mold Breaker'
df.loc[df.name == 'Basculin-Blue', 'ability1'] = 'Rock Head'
df.loc[df.name == 'Basculin-Blue', 'ability2'] = 'Adaptability'
df.loc[df.name == 'Basculin-Blue', 'ability3'] = 'Mold Breaker'

df = df.drop(['types', 'abilities'], axis=1)
df.columns = [
    'Name', 'Tier', 'HP', 'Attack', 'Defense', 'Special Attack',
    'Special Defense', 'Speed', 'Next Evolution(s)', 'Moves',
    'Evolutionary Stage', 'Num Evolutionary Stages', 'Evolutionary Progress',
    'Is Mega Evolution', 'Is Alternate Form', 'Num Moves', 'Base Stat Total',
    'Has Negative Ability', 'Type 1', 'Type 2', 'Num Types', 'Num Abilities',
    'Ability 1', 'Ability 2', 'Ability 3'
]

df = df[[
    'Name', 'Tier', 'Num Types', 'Type 1', 'Type 2', 'Num Abilities',
    'Ability 1', 'Ability 2', 'Ability 3', 'Has Negative Ability', 'HP',
    'Attack', 'Defense', 'Special Attack', 'Special Defense', 'Speed',
    'Base Stat Total', 'Next Evolution(s)', 'Evolutionary Stage',
    'Num Evolutionary Stages', 'Evolutionary Progress', 'Is Mega Evolution',
    'Is Alternate Form', 'Num Moves', 'Moves'
]]

mdf = mdf.set_index('name')

defense_increasing = {
    'Acid Armor': 2,
    'Barrier': 2,
    ' Cotton Guard': 3,
    'Iron Defense': 2,
    'Stockpile': 2,
    'Amnesia': 2,
    'Coil': 1,
    'Bulk Up': 1,
    'Clangorous Soulblaze': 2,
    'Cosmic Power': 2,
    'Defend Order': 2,
    'Calm Mind': 1,
    'Geomancy': 2,
    'Quiver Dance': 1,
}
attack_increasing = {
    'Coil': 1,
    'Hone Claws': 2,
    'Belly Drum': 6,
    'Bulk Up': 1,
    'Clangorous Soulblaze': 3,
    'Dragon Dance': 2,
    'Shell Smash': 6,
    'Shift Gear': 3,
    'Swords Dance': 2,
    'Work Up': 2,
    'Calm Mind': 1,
    'Geomancy': 4,
    'Nasty Plot': 2,
    'Quiver Dance': 2,
    'Tail Glow': 3,
    'Agility': 2,
    'Automize': 2,
    'Rock Polish': 2
}


def max_def_amt(moves):
    return max(defense_increasing.get(move, 0) for move in moves)


def max_atk_amt(moves):
    return max(attack_increasing.get(move, 0) for move in moves)


df['Defensive Boost Moves'] = df.Moves.map(
    lambda x: x.intersection(defense_increasing.keys()))
df['Offensive Boost Moves'] = df.Moves.map(
    lambda x: x.intersection(attack_increasing.keys()))
df['Max Defensive Boost Amount'] = df.Moves.map(max_def_amt)
df['Max Offensive Boost Amount'] = df.Moves.map(max_atk_amt)

recovery = {
    'Heal Order', 'Milk Drink', 'Moonlight', 'Morning Sun', 'Purify', 'Recover',
    'Roost', 'Shore Up', 'Slack Off', 'Soft-Boiled', 'Synthesis',
    'Strength Sap', 'Wish'
}
df['Recovery Moves'] = df.Moves.map(lambda moves: moves.intersection(recovery))

priority = {
    'Fake Out', 'Extreme Speed', 'Feint', 'Aqua Jet', 'Bullet Punch',
    'Ice Shard', 'Accelerock', 'Mach Punch', 'Shadow Sneak', 'Sucker Punch',
    'Vacuum Wave', 'Water Shuriken'
}


def high_priority_stabs(x):
    hps_moves = set()
    for m in x.Moves.intersection(priority):
        if mdf.loc[m, 'type'] in {x['Type 1'], x['Type 2']}:
            hps_moves.add(m)
    return hps_moves


df['Priority STAB Attacks'] = df.apply(high_priority_stabs, axis=1)

entry_hazards = {'Toxic Spikes', 'Stealth Rock', 'Spikes'}
df['Entry Hazards'] = df.Moves.map(lambda x: x.intersection(entry_hazards))

hazard_clear = {'Rapid Spin', 'Defog'}  #we may later exclude/add defog
df['Hazard Clearing Moves'] = df.Moves.map(
    lambda x: x.intersection(hazard_clear))

phazing_moves = {'Roar', 'Whirlwind', 'Dragon Tail', 'Circle Throw'}
df['Phazing Moves'] = df.Moves.map(lambda x: x.intersection(phazing_moves))

switch_attack = {'U-turn', 'Volt Switch'}
df['Switch Attacks'] = df.Moves.map(lambda x: x.intersection(switch_attack))

#strong moves (>65 power) that have a >30% chance of causing side effects with an accuracy over 85%
high_side_fx_prob = {
    'Steam Eruption', 'Sludge Bomb', 'Lava Plume', 'Iron Tail', 'Searing Shot',
    'Rolling Kick', 'Rock Slide', 'Poison Jab', 'Muddy Water', 'Iron Head',
    'Icicle Crash', 'Headbutt', 'Gunk Shot', 'Discharge', 'Body Slam',
    'Air Slash'
}
df['High Prob Side FX Attacks'] = df.Moves.map(
    lambda x: x.intersection(high_side_fx_prob))

constant_dmg = {'Seismic Toss', 'Night Shade'}
df['Constant Damage Attacks'] = df.Moves.map(
    lambda x: x.intersection(constant_dmg))

trapping_move = {'Mean Look', 'Block', 'Spider Web'}
df['Trapping Moves'] = df.Moves.map(lambda x: x.intersection(trapping_move))

df = df.sort_values('Name').set_index('Name')

print('Final dataset shape: ', df.shape)

df.to_csv('pokemon-data-cleaned.csv')
