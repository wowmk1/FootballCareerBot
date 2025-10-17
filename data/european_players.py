# european_players.py

# -------------------
# Champions League 2024
# -------------------

TEAM_ROSTERS = {
    # --- Spain ---
    'real_madrid': {
        'name': 'Real Madrid',
        'country': 'Spain',
        'league': 'Champions League',
        'players': [
            {'name': 'Thibaut Courtois', 'pos': 'GK', 'age': 32, 'rating': 89, 'nat': 'Belgium'},
            {'name': 'Andriy Lunin', 'pos': 'GK', 'age': 25, 'rating': 79, 'nat': 'Ukraine'},
            {'name': 'Antonio Rüdiger', 'pos': 'CB', 'age': 31, 'rating': 87, 'nat': 'Germany'},
            {'name': 'Éder Militão', 'pos': 'CB', 'age': 26, 'rating': 85, 'nat': 'Brazil'},
            {'name': 'David Alaba', 'pos': 'CB', 'age': 32, 'rating': 84, 'nat': 'Austria'},
            {'name': 'Nacho Fernández', 'pos': 'CB', 'age': 34, 'rating': 82, 'nat': 'Spain'},
            {'name': 'Dani Carvajal', 'pos': 'RB', 'age': 32, 'rating': 85, 'nat': 'Spain'},
            {'name': 'Ferland Mendy', 'pos': 'LB', 'age': 29, 'rating': 83, 'nat': 'France'},
            {'name': 'Lucas Vázquez', 'pos': 'RB', 'age': 33, 'rating': 79, 'nat': 'Spain'},
            {'name': 'Jude Bellingham', 'pos': 'CM', 'age': 21, 'rating': 90, 'nat': 'England'},
            {'name': 'Federico Valverde', 'pos': 'CM', 'age': 26, 'rating': 88, 'nat': 'Uruguay'},
            {'name': 'Eduardo Camavinga', 'pos': 'CM', 'age': 22, 'rating': 84, 'nat': 'France'},
            {'name': 'Aurélien Tchouaméni', 'pos': 'CDM', 'age': 24, 'rating': 85, 'nat': 'France'},
            {'name': 'Luka Modrić', 'pos': 'CM', 'age': 39, 'rating': 83, 'nat': 'Croatia'},
            {'name': 'Toni Kroos', 'pos': 'CM', 'age': 34, 'rating': 87, 'nat': 'Germany'},
            {'name': 'Kylian Mbappé', 'pos': 'W', 'age': 25, 'rating': 92, 'nat': 'France'},
            {'name': 'Vinícius Júnior', 'pos': 'W', 'age': 24, 'rating': 91, 'nat': 'Brazil'},
            {'name': 'Rodrygo', 'pos': 'W', 'age': 23, 'rating': 85, 'nat': 'Brazil'},
            {'name': 'Joselu', 'pos': 'ST', 'age': 34, 'rating': 78, 'nat': 'Spain'},
            {'name': 'Brahim Díaz', 'pos': 'CAM', 'age': 25, 'rating': 80, 'nat': 'Spain'},
        ]
    },

    'barcelona': {
        'name': 'Barcelona',
        'country': 'Spain',
        'league': 'Champions League',
        'players': [
            {'name': 'Marc-André ter Stegen', 'pos': 'GK', 'age': 32, 'rating': 88, 'nat': 'Germany'},
            {'name': 'Inaki Peña', 'pos': 'GK', 'age': 24, 'rating': 75, 'nat': 'Spain'},
            {'name': 'Ronald Araújo', 'pos': 'CB', 'age': 25, 'rating': 85, 'nat': 'Uruguay'},
            {'name': 'Jules Koundé', 'pos': 'CB', 'age': 25, 'rating': 84, 'nat': 'France'},
            {'name': 'Andreas Christensen', 'pos': 'CB', 'age': 27, 'rating': 83, 'nat': 'Denmark'},
            {'name': 'Alejandro Balde', 'pos': 'LB', 'age': 20, 'rating': 81, 'nat': 'Spain'},
            {'name': 'Sergi Roberto', 'pos': 'RB', 'age': 32, 'rating': 80, 'nat': 'Spain'},
            {'name': 'Gavi', 'pos': 'CM', 'age': 19, 'rating': 86, 'nat': 'Spain'},
            {'name': 'Pedri', 'pos': 'CM', 'age': 21, 'rating': 87, 'nat': 'Spain'},
            {'name': 'Frenkie de Jong', 'pos': 'CDM', 'age': 26, 'rating': 85, 'nat': 'Netherlands'},
            {'name': 'Robert Lewandowski', 'pos': 'ST', 'age': 36, 'rating': 87, 'nat': 'Poland'},
            {'name': 'Ousmane Dembélé', 'pos': 'W', 'age': 26, 'rating': 84, 'nat': 'France'},
            {'name': 'Raphinha', 'pos': 'W', 'age': 26, 'rating': 83, 'nat': 'Brazil'},
            {'name': 'Franck Kessié', 'pos': 'CM', 'age': 27, 'rating': 83, 'nat': 'Ivory Coast'},
            {'name': 'André Onana', 'pos': 'GK', 'age': 27, 'rating': 84, 'nat': 'Cameroon'},
        ]
    },

    'atletico_madrid': {
        'name': 'Atlético Madrid',
        'country': 'Spain',
        'league': 'Champions League',
        'players': [
            {'name': 'Jan Oblak', 'pos': 'GK', 'age': 31, 'rating': 90, 'nat': 'Slovenia'},
            {'name': 'Ivo Grbić', 'pos': 'GK', 'age': 26, 'rating': 76, 'nat': 'Croatia'},
            {'name': 'José María Giménez', 'pos': 'CB', 'age': 28, 'rating': 84, 'nat': 'Uruguay'},
            {'name': 'Stefan Savić', 'pos': 'CB', 'age': 33, 'rating': 82, 'nat': 'Montenegro'},
            {'name': 'Mario Hermoso', 'pos': 'CB', 'age': 28, 'rating': 81, 'nat': 'Spain'},
            {'name': 'Kieran Trippier', 'pos': 'RB', 'age': 33, 'rating': 82, 'nat': 'England'},
            {'name': 'Renan Lodi', 'pos': 'LB', 'age': 25, 'rating': 81, 'nat': 'Brazil'},
            {'name': 'Koke', 'pos': 'CM', 'age': 31, 'rating': 83, 'nat': 'Spain'},
            {'name': 'Rodrigo De Paul', 'pos': 'CM', 'age': 29, 'rating': 84, 'nat': 'Argentina'},
            {'name': 'João Félix', 'pos': 'ST', 'age': 24, 'rating': 84, 'nat': 'Portugal'},
            {'name': 'Antoine Griezmann', 'pos': 'W', 'age': 33, 'rating': 83, 'nat': 'France'},
            {'name': 'Ángel Correa', 'pos': 'W', 'age': 28, 'rating': 82, 'nat': 'Argentina'},
        ]
    },

    'sevilla': {
        'name': 'Sevilla',
        'country': 'Spain',
        'league': 'Champions League',
        'players': [
            {'name': 'Yassine Bounou', 'pos': 'GK', 'age': 33, 'rating': 83, 'nat': 'Morocco'},
            {'name': 'Marko Dmitrović', 'pos': 'GK', 'age': 32, 'rating': 79, 'nat': 'Serbia'},
            {'name': 'Diego Carlos', 'pos': 'CB', 'age': 30, 'rating': 84, 'nat': 'Brazil'},
            {'name': 'Jules Koundé', 'pos': 'CB', 'age': 25, 'rating': 84, 'nat': 'France'},
            {'name': 'Gonzalo Montiel', 'pos': 'RB', 'age': 26, 'rating': 82, 'nat': 'Argentina'},
            {'name': 'Alejandro Gómez', 'pos': 'CAM', 'age': 34, 'rating': 83, 'nat': 'Argentina'},
            {'name': 'Fernando', 'pos': 'CDM', 'age': 33, 'rating': 82, 'nat': 'Brazil'},
            {'name': 'Ivan Rakitić', 'pos': 'CM', 'age': 36, 'rating': 81, 'nat': 'Croatia'},
            {'name': 'Jesús Navas', 'pos': 'RB', 'age': 38, 'rating': 79, 'nat': 'Spain'},
            {'name': 'Youssef En-Nesyri', 'pos': 'ST', 'age': 27, 'rating': 84, 'nat': 'Morocco'},
            {'name': 'Lucas Ocampos', 'pos': 'W', 'age': 28, 'rating': 83, 'nat': 'Argentina'},
            {'name': 'Rony Lopes', 'pos': 'W', 'age': 26, 'rating': 81, 'nat': 'Portugal'},
        ]
    },

    # --- Germany ---
    'bayern_munich': {
        'name': 'Bayern Munich',
        'country': 'Germany',
        'league': 'Champions League',
        'players': [
            {'name': 'Manuel Neuer', 'pos': 'GK', 'age': 37, 'rating': 90, 'nat': 'Germany'},
            {'name': 'Alexander Nübel', 'pos': 'GK', 'age': 27, 'rating': 80, 'nat': 'Germany'},
            {'name': 'Dayot Upamecano', 'pos': 'CB', 'age': 25, 'rating': 85, 'nat': 'France'},
            {'name': 'Matthijs de Ligt', 'pos': 'CB', 'age': 25, 'rating': 86, 'nat': 'Netherlands'},
            {'name': 'Lucas Hernández', 'pos': 'LB', 'age': 27, 'rating': 83, 'nat': 'France'},
            {'name': 'Benjamin Pavard', 'pos': 'RB', 'age': 27, 'rating': 82, 'nat': 'France'},
            {'name': 'Joshua Kimmich', 'pos': 'CDM', 'age': 28, 'rating': 90, 'nat': 'Germany'},
            {'name': 'Leon Goretzka', 'pos': 'CM', 'age': 29, 'rating': 87, 'nat': 'Germany'},
            {'name': 'Jamal Musiala', 'pos': 'CAM', 'age': 21, 'rating': 87, 'nat': 'Germany'},
            {'name': 'Serge Gnabry', 'pos': 'W', 'age': 27, 'rating': 85, 'nat': 'Germany'},
            {'name': 'Leroy Sané', 'pos': 'W', 'age': 28, 'rating': 86, 'nat': 'Germany'},
            {'name': 'Harry Kane', 'pos': 'ST', 'age': 31, 'rating': 89, 'nat': 'England'},
        ]
    },
}

# -------------------
# Champions League 2024 (continued)
# -------------------

TEAM_ROSTERS.update({

    'borussia_dortmund': {
        'name': 'Borussia Dortmund',
        'country': 'Germany',
        'league': 'Champions League',
        'players': [
            {'name': 'Gregor Kobel', 'pos': 'GK', 'age': 25, 'rating': 85, 'nat': 'Switzerland'},
            {'name': 'Marwin Hitz', 'pos': 'GK', 'age': 36, 'rating': 78, 'nat': 'Switzerland'},
            {'name': 'Mats Hummels', 'pos': 'CB', 'age': 35, 'rating': 84, 'nat': 'Germany'},
            {'name': 'Niklas Süle', 'pos': 'CB', 'age': 28, 'rating': 84, 'nat': 'Germany'},
            {'name': 'Manuel Akanji', 'pos': 'CB', 'age': 27, 'rating': 83, 'nat': 'Switzerland'},
            {'name': 'Raphaël Guerreiro', 'pos': 'LB', 'age': 28, 'rating': 83, 'nat': 'Portugal'},
            {'name': 'Thomas Meunier', 'pos': 'RB', 'age': 32, 'rating': 81, 'nat': 'Belgium'},
            {'name': 'Jude Bellingham', 'pos': 'CM', 'age': 21, 'rating': 90, 'nat': 'England'},
            {'name': 'Marco Reus', 'pos': 'CAM', 'age': 34, 'rating': 84, 'nat': 'Germany'},
            {'name': 'Julian Brandt', 'pos': 'W', 'age': 26, 'rating': 84, 'nat': 'Germany'},
            {'name': 'Youssoufa Moukoko', 'pos': 'ST', 'age': 18, 'rating': 78, 'nat': 'Germany'},
        ]
    },

    'rb_leipzig': {
        'name': 'RB Leipzig',
        'country': 'Germany',
        'league': 'Champions League',
        'players': [
            {'name': 'Peter Gulacsi', 'pos': 'GK', 'age': 34, 'rating': 83, 'nat': 'Hungary'},
            {'name': 'Janis Blaswich', 'pos': 'GK', 'age': 31, 'rating': 79, 'nat': 'Germany'},
            {'name': 'Willi Orbán', 'pos': 'CB', 'age': 28, 'rating': 84, 'nat': 'Hungary'},
            {'name': 'Josko Gvardiol', 'pos': 'CB', 'age': 22, 'rating': 86, 'nat': 'Croatia'},
            {'name': 'Benjamin Henrichs', 'pos': 'RB', 'age': 26, 'rating': 81, 'nat': 'Germany'},
            {'name': 'Nordi Mukiele', 'pos': 'RB', 'age': 26, 'rating': 82, 'nat': 'France'},
            {'name': 'Angeliño', 'pos': 'LB', 'age': 25, 'rating': 81, 'nat': 'Spain'},
            {'name': 'Dominik Szoboszlai', 'pos': 'CM', 'age': 23, 'rating': 85, 'nat': 'Hungary'},
            {'name': 'Kevin Kampl', 'pos': 'CM', 'age': 33, 'rating': 81, 'nat': 'Slovenia'},
            {'name': 'Christopher Nkunku', 'pos': 'W', 'age': 25, 'rating': 88, 'nat': 'France'},
            {'name': 'Yussuf Poulsen', 'pos': 'ST', 'age': 29, 'rating': 82, 'nat': 'Denmark'},
        ]
    },

    'bayer_leverkusen': {
        'name': 'Bayer Leverkusen',
        'country': 'Germany',
        'league': 'Champions League',
        'players': [
            {'name': 'Lukáš Hrádecký', 'pos': 'GK', 'age': 34, 'rating': 83, 'nat': 'Finland'},
            {'name': 'André Ramalho', 'pos': 'CB', 'age': 30, 'rating': 80, 'nat': 'Brazil'},
            {'name': 'Jonathan Tah', 'pos': 'CB', 'age': 27, 'rating': 83, 'nat': 'Germany'},
            {'name': 'Mitchel Bakker', 'pos': 'LB', 'age': 22, 'rating': 79, 'nat': 'Netherlands'},
            {'name': 'Jeremiah St. Juste', 'pos': 'CB', 'age': 26, 'rating': 81, 'nat': 'Netherlands'},
            {'name': 'Wendell', 'pos': 'LB', 'age': 29, 'rating': 81, 'nat': 'Brazil'},
            {'name': 'Jeremie Frimpong', 'pos': 'RB', 'age': 22, 'rating': 81, 'nat': 'Netherlands'},
            {'name': 'Exequiel Palacios', 'pos': 'CM', 'age': 25, 'rating': 83, 'nat': 'Argentina'},
            {'name': 'Florian Wirtz', 'pos': 'CAM', 'age': 20, 'rating': 85, 'nat': 'Germany'},
            {'name': 'Karim Bellarabi', 'pos': 'W', 'age': 33, 'rating': 81, 'nat': 'Germany'},
            {'name': 'Patrik Schick', 'pos': 'ST', 'age': 27, 'rating': 84, 'nat': 'Czech Republic'},
        ]
    },

    # --- Italy ---
    'inter_milan': {
        'name': 'Inter Milan',
        'country': 'Italy',
        'league': 'Champions League',
        'players': [
            {'name': 'Samir Handanović', 'pos': 'GK', 'age': 40, 'rating': 86, 'nat': 'Slovenia'},
            {'name': 'André Onana', 'pos': 'GK', 'age': 27, 'rating': 84, 'nat': 'Cameroon'},
            {'name': 'Milan Škriniar', 'pos': 'CB', 'age': 28, 'rating': 85, 'nat': 'Slovakia'},
            {'name': 'Stefan de Vrij', 'pos': 'CB', 'age': 31, 'rating': 84, 'nat': 'Netherlands'},
            {'name': 'Alessandro Bastoni', 'pos': 'CB', 'age': 25, 'rating': 85, 'nat': 'Italy'},
            {'name': 'Denzel Dumfries', 'pos': 'RB', 'age': 27, 'rating': 83, 'nat': 'Netherlands'},
            {'name': 'Robin Gosens', 'pos': 'LB', 'age': 29, 'rating': 82, 'nat': 'Germany'},
            {'name': 'Nicolo Barella', 'pos': 'CM', 'age': 26, 'rating': 87, 'nat': 'Italy'},
            {'name': 'Marcelo Brozović', 'pos': 'CDM', 'age': 31, 'rating': 85, 'nat': 'Croatia'},
            {'name': 'Lautaro Martínez', 'pos': 'ST', 'age': 26, 'rating': 87, 'nat': 'Argentina'},
            {'name': 'Hakan Çalhanoğlu', 'pos': 'CAM', 'age': 29, 'rating': 84, 'nat': 'Turkey'},
        ]
    },

    'ac_milan': {
        'name': 'AC Milan',
        'country': 'Italy',
        'league': 'Champions League',
        'players': [
            {'name': 'Mike Maignan', 'pos': 'GK', 'age': 28, 'rating': 87, 'nat': 'France'},
            {'name': 'Ciprian Tătărușanu', 'pos': 'GK', 'age': 37, 'rating': 78, 'nat': 'Romania'},
            {'name': 'Fikayo Tomori', 'pos': 'CB', 'age': 25, 'rating': 84, 'nat': 'England'},
            {'name': 'Pierre Kalulu', 'pos': 'CB', 'age': 23, 'rating': 81, 'nat': 'France'},
            {'name': 'Alessio Romagnoli', 'pos': 'CB', 'age': 28, 'rating': 82, 'nat': 'Italy'},
            {'name': 'Theo Hernández', 'pos': 'LB', 'age': 26, 'rating': 86, 'nat': 'France'},
            {'name': 'Davide Calabria', 'pos': 'RB', 'age': 27, 'rating': 81, 'nat': 'Italy'},
            {'name': 'Sandro Tonali', 'pos': 'CM', 'age': 23, 'rating': 85, 'nat': 'Italy'},
            {'name': 'Rafael Leão', 'pos': 'W', 'age': 24, 'rating': 87, 'nat': 'Portugal'},
            {'name': 'Olivier Giroud', 'pos': 'ST', 'age': 37, 'rating': 82, 'nat': 'France'},
            {'name': 'Brahim Díaz', 'pos': 'CAM', 'age': 25, 'rating': 80, 'nat': 'Spain'},
        ]
    },

})

# -------------------
# Champions League 2024 (continued)
# -------------------

TEAM_ROSTERS.update({

    # --- Italy ---
    'juventus': {
        'name': 'Juventus',
        'country': 'Italy',
        'league': 'Champions League',
        'players': [
            {'name': 'Wojciech Szczęsny', 'pos': 'GK', 'age': 35, 'rating': 86, 'nat': 'Poland'},
            {'name': 'Mattia Perin', 'pos': 'GK', 'age': 32, 'rating': 79, 'nat': 'Italy'},
            {'name': 'Leonardo Bonucci', 'pos': 'CB', 'age': 37, 'rating': 84, 'nat': 'Italy'},
            {'name': 'Gleison Bremer', 'pos': 'CB', 'age': 27, 'rating': 85, 'nat': 'Brazil'},
            {'name': 'Danilo', 'pos': 'RB', 'age': 32, 'rating': 83, 'nat': 'Brazil'},
            {'name': 'Alex Sandro', 'pos': 'LB', 'age': 33, 'rating': 82, 'nat': 'Brazil'},
            {'name': 'Paul Pogba', 'pos': 'CM', 'age': 31, 'rating': 85, 'nat': 'France'},
            {'name': 'Manuel Locatelli', 'pos': 'CDM', 'age': 26, 'rating': 84, 'nat': 'Italy'},
            {'name': 'Adrien Rabiot', 'pos': 'CM', 'age': 28, 'rating': 83, 'nat': 'France'},
            {'name': 'Dusan Vlahovic', 'pos': 'ST', 'age': 24, 'rating': 87, 'nat': 'Serbia'},
            {'name': 'Federico Chiesa', 'pos': 'W', 'age': 25, 'rating': 86, 'nat': 'Italy'},
        ]
    },

    'napoli': {
        'name': 'Napoli',
        'country': 'Italy',
        'league': 'Champions League',
        'players': [
            {'name': 'Alex Meret', 'pos': 'GK', 'age': 26, 'rating': 82, 'nat': 'Italy'},
            {'name': 'David Ospina', 'pos': 'GK', 'age': 35, 'rating': 81, 'nat': 'Colombia'},
            {'name': 'Koulibaly', 'pos': 'CB', 'age': 32, 'rating': 86, 'nat': 'Senegal'},
            {'name': 'Giovanni Di Lorenzo', 'pos': 'RB', 'age': 29, 'rating': 84, 'nat': 'Italy'},
            {'name': 'Mario Rui', 'pos': 'LB', 'age': 31, 'rating': 81, 'nat': 'Portugal'},
            {'name': 'Kim Min-jae', 'pos': 'CB', 'age': 26, 'rating': 85, 'nat': 'South Korea'},
            {'name': 'Andre-Frank Zambo Anguissa', 'pos': 'CDM', 'age': 27, 'rating': 83, 'nat': 'Cameroon'},
            {'name': 'Piotr Zieliński', 'pos': 'CM', 'age': 29, 'rating': 85, 'nat': 'Poland'},
            {'name': 'Hirving Lozano', 'pos': 'W', 'age': 27, 'rating': 84, 'nat': 'Mexico'},
            {'name': 'Victor Osimhen', 'pos': 'ST', 'age': 25, 'rating': 87, 'nat': 'Nigeria'},
            {'name': 'Khvicha Kvaratskhelia', 'pos': 'W', 'age': 22, 'rating': 86, 'nat': 'Georgia'},
        ]
    },

    # --- France ---
    'paris_saint_germain': {
        'name': 'Paris Saint-Germain',
        'country': 'France',
        'league': 'Champions League',
        'players': [
            {'name': 'Gianluigi Donnarumma', 'pos': 'GK', 'age': 25, 'rating': 88, 'nat': 'Italy'},
            {'name': 'Navas', 'pos': 'GK', 'age': 36, 'rating': 84, 'nat': 'Costa Rica'},
            {'name': 'Marquinhos', 'pos': 'CB', 'age': 29, 'rating': 87, 'nat': 'Brazil'},
            {'name': 'Sergio Ramos', 'pos': 'CB', 'age': 37, 'rating': 82, 'nat': 'Spain'},
            {'name': 'Presnel Kimpembe', 'pos': 'CB', 'age': 27, 'rating': 84, 'nat': 'France'},
            {'name': 'Achraf Hakimi', 'pos': 'RB', 'age': 25, 'rating': 87, 'nat': 'Morocco'},
            {'name': 'Nuno Mendes', 'pos': 'LB', 'age': 21, 'rating': 84, 'nat': 'Portugal'},
            {'name': 'Marco Verratti', 'pos': 'CM', 'age': 31, 'rating': 86, 'nat': 'Italy'},
            {'name': 'Vitinha', 'pos': 'CM', 'age': 23, 'rating': 83, 'nat': 'Portugal'},
            {'name': 'Lionel Messi', 'pos': 'RW', 'age': 36, 'rating': 91, 'nat': 'Argentina'},
            {'name': 'Kylian Mbappé', 'pos': 'ST', 'age': 25, 'rating': 92, 'nat': 'France'},
        ]
    },

    'marseille': {
        'name': 'Marseille',
        'country': 'France',
        'league': 'Champions League',
        'players': [
            {'name': 'Pau López', 'pos': 'GK', 'age': 28, 'rating': 82, 'nat': 'Spain'},
            {'name': 'Stefan Bajic', 'pos': 'GK', 'age': 22, 'rating': 75, 'nat': 'France'},
            {'name': 'William Saliba', 'pos': 'CB', 'age': 22, 'rating': 85, 'nat': 'France'},
            {'name': 'Leonardo Balerdi', 'pos': 'CB', 'age': 24, 'rating': 81, 'nat': 'Argentina'},
            {'name': 'Luan Peres', 'pos': 'LB', 'age': 28, 'rating': 80, 'nat': 'Brazil'},
            {'name': 'Sead Kolašinac', 'pos': 'LB', 'age': 30, 'rating': 81, 'nat': 'Bosnia'},
            {'name': 'Boubacar Kamara', 'pos': 'CDM', 'age': 24, 'rating': 83, 'nat': 'France'},
            {'name': 'Mattéo Guendouzi', 'pos': 'CM', 'age': 24, 'rating': 82, 'nat': 'France'},
            {'name': 'Cengiz Ünder', 'pos': 'RW', 'age': 25, 'rating': 83, 'nat': 'Turkey'},
            {'name': 'Jonathan David', 'pos': 'ST', 'age': 24, 'rating': 86, 'nat': 'Canada'},
            {'name': 'Pol Lirola', 'pos': 'RB', 'age': 25, 'rating': 81, 'nat': 'Spain'},
        ]
    },

    'monaco': {
        'name': 'Monaco',
        'country': 'France',
        'league': 'Champions League',
        'players': [
            {'name': 'Alexander Nübel', 'pos': 'GK', 'age': 27, 'rating': 80, 'nat': 'Germany'},
            {'name': 'Loïc Badiashile', 'pos': 'GK', 'age': 22, 'rating': 74, 'nat': 'France'},
            {'name': 'Axel Disasi', 'pos': 'CB', 'age': 25, 'rating': 83, 'nat': 'France'},
            {'name': 'Caio Henrique', 'pos': 'LB', 'age': 26, 'rating': 81, 'nat': 'Brazil'},
            {'name': 'Djibril Sidibé', 'pos': 'RB', 'age': 31, 'rating': 80, 'nat': 'France'},
            {'name': 'Wenderson', 'pos': 'CB', 'age': 22, 'rating': 78, 'nat': 'Brazil'},
            {'name': 'Youssouf Fofana', 'pos': 'CM', 'age': 25, 'rating': 82, 'nat': 'France'},
            {'name': 'Aurélien Tchouaméni', 'pos': 'CM', 'age': 24, 'rating': 85, 'nat': 'France'},
            {'name': 'Kevin Volland', 'pos': 'ST', 'age': 31, 'rating': 83, 'nat': 'Germany'},
            {'name': 'Myles Roux', 'pos': 'RW', 'age': 22, 'rating': 77, 'nat': 'France'},
            {'name': 'Gelson Martins', 'pos': 'W', 'age': 30, 'rating': 80, 'nat': 'Portugal'},
        ]
    },

    'lyon': {
        'name': 'Lyon',
        'country': 'France',
        'league': 'Champions League',
        'players': [
            {'name': 'Anthony Lopes', 'pos': 'GK', 'age': 32, 'rating': 84, 'nat': 'Portugal'},
            {'name': 'Julian Pollersbeck', 'pos': 'GK', 'age': 29, 'rating': 78, 'nat': 'Germany'},
            {'name': 'Castello Lukeba', 'pos': 'CB', 'age': 21, 'rating': 82, 'nat': 'France'},
            {'name': 'Sinaly Diomandé', 'pos': 'CB', 'age': 23, 'rating': 79, 'nat': 'France'},
            {'name': 'Maxwel Cornet', 'pos': 'LB', 'age': 26, 'rating': 82, 'nat': 'Ivory Coast'},
            {'name': 'Léo Dubois', 'pos': 'RB', 'age': 28, 'rating': 81, 'nat': 'France'},
            {'name': 'Lucas Paquetá', 'pos': 'CM', 'age': 25, 'rating': 84, 'nat': 'Brazil'},
            {'name': 'Tanguy Ndombele', 'pos': 'CM', 'age': 27, 'rating': 83, 'nat': 'France'},
            {'name': 'Rayan Cherki', 'pos': 'CAM', 'age': 20, 'rating': 80, 'nat': 'France'},
            {'name': 'Karl Toko Ekambi', 'pos': 'ST', 'age': 29, 'rating': 82, 'nat': 'Cameroon'},
            {'name': 'Paquetá', 'pos': 'W', 'age': 25, 'rating': 84, 'nat': 'Brazil'},
        ]
    },

})

# -------------------
# Champions League 2024 (continued)
# -------------------

TEAM_ROSTERS.update({

    # --- Portugal ---
    'benfica': {
        'name': 'Benfica',
        'country': 'Portugal',
        'league': 'Champions League',
        'players': [
            {'name': 'Odysseas Vlachodimos', 'pos': 'GK', 'age': 28, 'rating': 82, 'nat': 'Greece'},
            {'name': 'Altay Bayındır', 'pos': 'GK', 'age': 25, 'rating': 79, 'nat': 'Turkey'},
            {'name': 'Nicolás Otamendi', 'pos': 'CB', 'age': 36, 'rating': 81, 'nat': 'Argentina'},
            {'name': 'Jan Vertonghen', 'pos': 'CB', 'age': 36, 'rating': 80, 'nat': 'Belgium'},
            {'name': 'Morato', 'pos': 'CB', 'age': 21, 'rating': 78, 'nat': 'Brazil'},
            {'name': 'Rafa Silva', 'pos': 'RW', 'age': 28, 'rating': 83, 'nat': 'Portugal'},
            {'name': 'Grimaldo', 'pos': 'LB', 'age': 28, 'rating': 83, 'nat': 'Spain'},
            {'name': 'Roman Yaremchuk', 'pos': 'ST', 'age': 27, 'rating': 82, 'nat': 'Ukraine'},
            {'name': 'Pizzi', 'pos': 'CM', 'age': 34, 'rating': 81, 'nat': 'Portugal'},
            {'name': 'Enzo Fernández', 'pos': 'CM', 'age': 23, 'rating': 84, 'nat': 'Argentina'},
            {'name': 'Gonçalo Ramos', 'pos': 'ST', 'age': 22, 'rating': 84, 'nat': 'Portugal'},
        ]
    },

    'porto': {
        'name': 'Porto',
        'country': 'Portugal',
        'league': 'Champions League',
        'players': [
            {'name': 'Diogo Costa', 'pos': 'GK', 'age': 24, 'rating': 85, 'nat': 'Portugal'},
            {'name': 'Agustín Marchesín', 'pos': 'GK', 'age': 36, 'rating': 82, 'nat': 'Argentina'},
            {'name': 'Pepe', 'pos': 'CB', 'age': 41, 'rating': 81, 'nat': 'Portugal'},
            {'name': 'David Carmo', 'pos': 'CB', 'age': 25, 'rating': 82, 'nat': 'Portugal'},
            {'name': 'Otávio', 'pos': 'CM', 'age': 27, 'rating': 84, 'nat': 'Brazil'},
            {'name': 'Mateus Uribe', 'pos': 'CM', 'age': 31, 'rating': 83, 'nat': 'Colombia'},
            {'name': 'Luis Díaz', 'pos': 'LW', 'age': 26, 'rating': 87, 'nat': 'Colombia'},
            {'name': 'Toni Martínez', 'pos': 'ST', 'age': 25, 'rating': 80, 'nat': 'Spain'},
            {'name': 'Wilson Manafá', 'pos': 'RB', 'age': 28, 'rating': 81, 'nat': 'Portugal'},
            {'name': 'Marcano', 'pos': 'CB', 'age': 33, 'rating': 80, 'nat': 'Spain'},
            {'name': 'Pepe', 'pos': 'CB', 'age': 41, 'rating': 81, 'nat': 'Portugal'},
        ]
    },

    'sporting_cp': {
        'name': 'Sporting CP',
        'country': 'Portugal',
        'league': 'Champions League',
        'players': [
            {'name': 'Antonio Adán', 'pos': 'GK', 'age': 36, 'rating': 81, 'nat': 'Spain'},
            {'name': 'Matheus Reis', 'pos': 'LB', 'age': 28, 'rating': 81, 'nat': 'Brazil'},
            {'name': 'Sebastián Coates', 'pos': 'CB', 'age': 33, 'rating': 82, 'nat': 'Uruguay'},
            {'name': 'Inácio', 'pos': 'CB', 'age': 21, 'rating': 78, 'nat': 'Portugal'},
            {'name': 'Pedro Porro', 'pos': 'RB', 'age': 23, 'rating': 82, 'nat': 'Spain'},
            {'name': 'Manuel Ugarte', 'pos': 'CDM', 'age': 22, 'rating': 83, 'nat': 'Uruguay'},
            {'name': 'João Palhinha', 'pos': 'CDM', 'age': 26, 'rating': 84, 'nat': 'Portugal'},
            {'name': 'Pedro Gonçalves', 'pos': 'CAM', 'age': 24, 'rating': 85, 'nat': 'Portugal'},
            {'name': 'Paulinho', 'pos': 'ST', 'age': 22, 'rating': 79, 'nat': 'Portugal'},
            {'name': 'Nuno Santos', 'pos': 'LW', 'age': 27, 'rating': 81, 'nat': 'Portugal'},
            {'name': 'Trincão', 'pos': 'RW', 'age': 23, 'rating': 80, 'nat': 'Portugal'},
        ]
    },

    # --- Netherlands ---
    'ajax': {
        'name': 'Ajax',
        'country': 'Netherlands',
        'league': 'Champions League',
        'players': [
            {'name': 'Remko Pasveer', 'pos': 'GK', 'age': 39, 'rating': 82, 'nat': 'Netherlands'},
            {'name': 'Stefan Ortega', 'pos': 'GK', 'age': 31, 'rating': 79, 'nat': 'Germany'},
            {'name': 'Jurrien Timber', 'pos': 'CB', 'age': 22, 'rating': 84, 'nat': 'Netherlands'},
            {'name': 'Lisandro Martínez', 'pos': 'CB', 'age': 25, 'rating': 85, 'nat': 'Argentina'},
            {'name': 'Daley Blind', 'pos': 'LB', 'age': 33, 'rating': 83, 'nat': 'Netherlands'},
            {'name': 'Nicolas Tagliafico', 'pos': 'LB', 'age': 30, 'rating': 81, 'nat': 'Argentina'},
            {'name': 'Edson Álvarez', 'pos': 'CDM', 'age': 25, 'rating': 83, 'nat': 'Mexico'},
            {'name': 'Steven Berghuis', 'pos': 'RW', 'age': 30, 'rating': 83, 'nat': 'Netherlands'},
            {'name': 'Dusan Tadic', 'pos': 'CAM', 'age': 35, 'rating': 84, 'nat': 'Serbia'},
            {'name': 'Brian Brobbey', 'pos': 'ST', 'age': 21, 'rating': 82, 'nat': 'Netherlands'},
            {'name': 'Sebastien Haller', 'pos': 'ST', 'age': 29, 'rating': 84, 'nat': 'Ivory Coast'},
        ]
    },

    'psv_eindhoven': {
        'name': 'PSV Eindhoven',
        'country': 'Netherlands',
        'league': 'Champions League',
        'players': [
            {'name': 'Walter Benítez', 'pos': 'GK', 'age': 30, 'rating': 81, 'nat': 'Argentina'},
            {'name': 'Jeroen Zoet', 'pos': 'GK', 'age': 31, 'rating': 79, 'nat': 'Netherlands'},
            {'name': 'Philipp Max', 'pos': 'LB', 'age': 29, 'rating': 81, 'nat': 'Germany'},
            {'name': 'Jordan Teze', 'pos': 'CB', 'age': 23, 'rating': 82, 'nat': 'Netherlands'},
            {'name': 'Timo Baumgartl', 'pos': 'CB', 'age': 27, 'rating': 81, 'nat': 'Germany'},
            {'name': 'Andre Ramalho', 'pos': 'CB', 'age': 30, 'rating': 80, 'nat': 'Brazil'},
            {'name': 'Cody Gakpo', 'pos': 'LW', 'age': 25, 'rating': 86, 'nat': 'Netherlands'},
            {'name': 'Xavi Simons', 'pos': 'CAM', 'age': 20, 'rating': 82, 'nat': 'Netherlands'},
            {'name': 'Mario Götze', 'pos': 'CM', 'age': 31, 'rating': 82, 'nat': 'Germany'},
            {'name': 'Luuk de Jong', 'pos': 'ST', 'age': 33, 'rating': 81, 'nat': 'Netherlands'},
            {'name': 'Noa Lang', 'pos': 'RW', 'age': 25, 'rating': 83, 'nat': 'Netherlands'},
        ]
    },

    'feyenoord': {
        'name': 'Feyenoord',
        'country': 'Netherlands',
        'league': 'Champions League',
        'players': [
            {'name': 'Justin Bijlow', 'pos': 'GK', 'age': 25, 'rating': 84, 'nat': 'Netherlands'},
            {'name': 'Nick Marsman', 'pos': 'GK', 'age': 34, 'rating': 78, 'nat': 'Netherlands'},
            {'name': 'Eric Botteghin', 'pos': 'CB', 'age': 37, 'rating': 79, 'nat': 'Netherlands'},
            {'name': 'Jeremiah St. Juste', 'pos': 'CB', 'age': 26, 'rating': 81, 'nat': 'Netherlands'},
            {'name': 'Tyrell Malacia', 'pos': 'LB', 'age': 24, 'rating': 82, 'nat': 'Netherlands'},
            {'name': 'Marcus Pedersen', 'pos': 'CB', 'age': 28, 'rating': 80, 'nat': 'Norway'},
            {'name': 'Orkun Kökçü', 'pos': 'CM', 'age': 23, 'rating': 84, 'nat': 'Turkey'},
            {'name': 'Leroy Fer', 'pos': 'CM', 'age': 32, 'rating': 81, 'nat': 'Netherlands'},
            {'name': 'Noa Lang', 'pos': 'RW', 'age': 25, 'rating': 83, 'nat': 'Netherlands'},
            {'name': 'Alireza Jahanbakhsh', 'pos': 'LW', 'age': 30, 'rating': 82, 'nat': 'Iran'},
            {'name': 'Luis Sinisterra', 'pos': 'ST', 'age': 24, 'rating': 84, 'nat': 'Colombia'},
        ]
    },

})

# -------------------
# Champions League 2024 (continued)
# -------------------

TEAM_ROSTERS.update({

    # --- Belgium ---
    'club_brugge': {
        'name': 'Club Brugge',
        'country': 'Belgium',
        'league': 'Champions League',
        'players': [
            {'name': 'Simon Mignolet', 'pos': 'GK', 'age': 36, 'rating': 82, 'nat': 'Belgium'},
            {'name': 'Ethan Horvath', 'pos': 'GK', 'age': 28, 'rating': 80, 'nat': 'USA'},
            {'name': 'Odilon Kossounou', 'pos': 'CB', 'age': 23, 'rating': 82, 'nat': 'Ivory Coast'},
            {'name': 'Matej Mitrović', 'pos': 'CB', 'age': 30, 'rating': 80, 'nat': 'Croatia'},
            {'name': 'Clinton Mata', 'pos': 'RB', 'age': 30, 'rating': 81, 'nat': 'Angola'},
            {'name': 'Karlo Letica', 'pos': 'GK', 'age': 27, 'rating': 78, 'nat': 'Croatia'},
            {'name': 'Hans Vanaken', 'pos': 'CM', 'age': 30, 'rating': 84, 'nat': 'Belgium'},
            {'name': 'Ruud Vormer', 'pos': 'CM', 'age': 34, 'rating': 82, 'nat': 'Netherlands'},
            {'name': 'Noa Lang', 'pos': 'RW', 'age': 25, 'rating': 83, 'nat': 'Netherlands'},
            {'name': 'Bas Dost', 'pos': 'ST', 'age': 34, 'rating': 81, 'nat': 'Netherlands'},
            {'name': 'Michael Krmencik', 'pos': 'ST', 'age': 28, 'rating': 79, 'nat': 'Czech Republic'},
        ]
    },

    'anderlecht': {
        'name': 'Anderlecht',
        'country': 'Belgium',
        'league': 'Champions League',
        'players': [
            {'name': 'Thomas Didillon', 'pos': 'GK', 'age': 28, 'rating': 80, 'nat': 'France'},
            {'name': 'Zeno Debast', 'pos': 'CB', 'age': 19, 'rating': 76, 'nat': 'Belgium'},
            {'name': 'Amadou Diawara', 'pos': 'CDM', 'age': 26, 'rating': 82, 'nat': 'Guinea'},
            {'name': 'Sambi Lokonga', 'pos': 'CM', 'age': 25, 'rating': 82, 'nat': 'Belgium'},
            {'name': 'Frank Acheampong', 'pos': 'RW', 'age': 27, 'rating': 81, 'nat': 'Ghana'},
            {'name': 'Adrien Trebel', 'pos': 'CM', 'age': 32, 'rating': 81, 'nat': 'France'},
            {'name': 'Paul Mukairu', 'pos': 'LW', 'age': 22, 'rating': 79, 'nat': 'Nigeria'},
            {'name': 'Ruben Santos', 'pos': 'RB', 'age': 24, 'rating': 80, 'nat': 'Belgium'},
            {'name': 'Jérémy Doku', 'pos': 'LW', 'age': 21, 'rating': 84, 'nat': 'Belgium'},
            {'name': 'Pierre-Yves Ngawa', 'pos': 'CB', 'age': 29, 'rating': 79, 'nat': 'Belgium'},
            {'name': 'Vladimir Coufal', 'pos': 'RB', 'age': 31, 'rating': 81, 'nat': 'Czech Republic'},
        ]
    },

    # --- Turkey ---
    'galatasaray': {
        'name': 'Galatasaray',
        'country': 'Turkey',
        'league': 'Champions League',
        'players': [
            {'name': 'Fernando Muslera', 'pos': 'GK', 'age': 37, 'rating': 83, 'nat': 'Uruguay'},
            {'name': 'Inaki Pena', 'pos': 'GK', 'age': 26, 'rating': 78, 'nat': 'Spain'},
            {'name': 'Victor Nelsson', 'pos': 'CB', 'age': 24, 'rating': 82, 'nat': 'Denmark'},
            {'name': 'Marcao', 'pos': 'CB', 'age': 28, 'rating': 83, 'nat': 'Brazil'},
            {'name': 'Omar Elabdellaoui', 'pos': 'RB', 'age': 31, 'rating': 80, 'nat': 'Norway'},
            {'name': 'Sacha Boey', 'pos': 'RB', 'age': 23, 'rating': 80, 'nat': 'France'},
            {'name': 'Lucas Torreira', 'pos': 'CDM', 'age': 27, 'rating': 84, 'nat': 'Uruguay'},
            {'name': 'Dries Mertens', 'pos': 'CAM', 'age': 36, 'rating': 83, 'nat': 'Belgium'},
            {'name': 'Kerem Aktürkoğlu', 'pos': 'LW', 'age': 24, 'rating': 84, 'nat': 'Turkey'},
            {'name': 'Enner Valencia', 'pos': 'ST', 'age': 33, 'rating': 82, 'nat': 'Ecuador'},
            {'name': 'Mostafa Mohamed', 'pos': 'ST', 'age': 26, 'rating': 81, 'nat': 'Egypt'},
        ]
    },

    'fenerbahce': {
        'name': 'Fenerbahçe',
        'country': 'Turkey',
        'league': 'Champions League',
        'players': [
            {'name': 'Altay Bayındır', 'pos': 'GK', 'age': 25, 'rating': 84, 'nat': 'Turkey'},
            {'name': 'Berke Özer', 'pos': 'GK', 'age': 24, 'rating': 78, 'nat': 'Turkey'},
            {'name': 'Attila Szalai', 'pos': 'CB', 'age': 25, 'rating': 83, 'nat': 'Hungary'},
            {'name': 'Szilveszter Hangya', 'pos': 'RB', 'age': 23, 'rating': 80, 'nat': 'Hungary'},
            {'name': 'Kim Min-jae', 'pos': 'CB', 'age': 26, 'rating': 85, 'nat': 'South Korea'},
            {'name': 'Caner Erkin', 'pos': 'LB', 'age': 35, 'rating': 79, 'nat': 'Turkey'},
            {'name': 'Miguel Crespo', 'pos': 'CM', 'age': 25, 'rating': 81, 'nat': 'Portugal'},
            {'name': 'Joshua King', 'pos': 'ST', 'age': 32, 'rating': 81, 'nat': 'Norway'},
            {'name': 'Enner Valencia', 'pos': 'ST', 'age': 33, 'rating': 82, 'nat': 'Ecuador'},
            {'name': 'Willian Arão', 'pos': 'CDM', 'age': 31, 'rating': 82, 'nat': 'Brazil'},
            {'name': 'Arda Güler', 'pos': 'CAM', 'age': 19, 'rating': 79, 'nat': 'Turkey'},
        ]
    },

    # --- Scotland ---
    'celtic': {
        'name': 'Celtic',
        'country': 'Scotland',
        'league': 'Champions League',
        'players': [
            {'name': 'Joe Hart', 'pos': 'GK', 'age': 37, 'rating': 80, 'nat': 'England'},
            {'name': 'Vasilis Barkas', 'pos': 'GK', 'age': 27, 'rating': 78, 'nat': 'Greece'},
            {'name': 'Cameron Carter-Vickers', 'pos': 'CB', 'age': 25, 'rating': 82, 'nat': 'USA'},
            {'name': 'Carl Starfelt', 'pos': 'CB', 'age': 27, 'rating': 81, 'nat': 'Sweden'},
            {'name': 'Anthony Ralston', 'pos': 'RB', 'age': 25, 'rating': 79, 'nat': 'Scotland'},
            {'name': 'Josip Juranović', 'pos': 'RB', 'age': 27, 'rating': 81, 'nat': 'Croatia'},
            {'name': 'Callum McGregor', 'pos': 'CM', 'age': 28, 'rating': 84, 'nat': 'Scotland'},
            {'name': 'David Turnbull', 'pos': 'CAM', 'age': 23, 'rating': 82, 'nat': 'Scotland'},
            {'name': 'Kyogo Furuhashi', 'pos': 'ST', 'age': 27, 'rating': 85, 'nat': 'Japan'},
            {'name': 'Liel Abada', 'pos': 'LW', 'age': 21, 'rating': 82, 'nat': 'Israel'},
            {'name': 'Reo Hatate', 'pos': 'CM', 'age': 25, 'rating': 81, 'nat': 'Japan'},
        ]
    },

    'rangers': {
        'name': 'Rangers',
        'country': 'Scotland',
        'league': 'Champions League',
        'players': [
            {'name': 'Jon McLaughlin', 'pos': 'GK', 'age': 36, 'rating': 78, 'nat': 'Scotland'},
            {'name': 'Allan McGregor', 'pos': 'GK', 'age': 41, 'rating': 77, 'nat': 'Scotland'},
            {'name': 'James Tavernier', 'pos': 'RB', 'age': 29, 'rating': 86, 'nat': 'England'},
            {'name': 'Leon Balogun', 'pos': 'CB', 'age': 35, 'rating': 81, 'nat': 'Nigeria'},
            {'name': 'Connor Goldson', 'pos': 'CB', 'age': 31, 'rating': 82, 'nat': 'England'},
            {'name': 'Nathan Patterson', 'pos': 'RB', 'age': 22, 'rating': 80, 'nat': 'Scotland'},
            {'name': 'Scott Arfield', 'pos': 'CM', 'age': 34, 'rating': 80, 'nat': 'Canada'},
            {'name': 'Joe Aribo', 'pos': 'CM', 'age': 25, 'rating': 82, 'nat': 'Nigeria'},
            {'name': 'Rangers Midfielder', 'pos': 'CAM', 'age': 24, 'rating': 81, 'nat': 'Scotland'},
            {'name': 'Morelos', 'pos': 'ST', 'age': 26, 'rating': 84, 'nat': 'Colombia'},
            {'name': 'Antonio Čolak', 'pos': 'ST', 'age': 29, 'rating': 81, 'nat': 'Croatia'},
        ]
    },

})


# -------------------
# Champions League 2024 (continued)
# -------------------

TEAM_ROSTERS.update({

    # --- Austria ---
    'rb_salzburg': {
        'name': 'RB Salzburg',
        'country': 'Austria',
        'league': 'Champions League',
        'players': [
            {'name': 'Cican Stankovic', 'pos': 'GK', 'age': 28, 'rating': 83, 'nat': 'Austria'},
            {'name': 'Andreas Ulmer', 'pos': 'LB', 'age': 37, 'rating': 80, 'nat': 'Austria'},
            {'name': 'Oumar Solet', 'pos': 'CB', 'age': 22, 'rating': 81, 'nat': 'France'},
            {'name': 'Rasmus Kristensen', 'pos': 'RB', 'age': 26, 'rating': 83, 'nat': 'Denmark'},
            {'name': 'Max Wöber', 'pos': 'CB', 'age': 25, 'rating': 82, 'nat': 'Austria'},
            {'name': 'László Bénes', 'pos': 'CM', 'age': 25, 'rating': 81, 'nat': 'Slovakia'},
            {'name': 'Benjamin Sesko', 'pos': 'ST', 'age': 20, 'rating': 84, 'nat': 'Slovenia'},
            {'name': 'Nico Mantl', 'pos': 'GK', 'age': 22, 'rating': 78, 'nat': 'Germany'},
            {'name': 'Noah Okafor', 'pos': 'LW', 'age': 23, 'rating': 82, 'nat': 'Switzerland'},
            {'name': 'Moini', 'pos': 'RW', 'age': 21, 'rating': 80, 'nat': 'Austria'},
            {'name': 'Dominik Szoboszlai', 'pos': 'CAM', 'age': 23, 'rating': 86, 'nat': 'Hungary'},
        ]
    },

    # --- Ukraine ---
    'shakhtar_donetsk': {
        'name': 'Shakhtar Donetsk',
        'country': 'Ukraine',
        'league': 'Champions League',
        'players': [
            {'name': 'Andriy Pyatov', 'pos': 'GK', 'age': 38, 'rating': 82, 'nat': 'Ukraine'},
            {'name': 'Heorhiy Bushchan', 'pos': 'GK', 'age': 27, 'rating': 81, 'nat': 'Ukraine'},
            {'name': 'Marcos Antonio', 'pos': 'CM', 'age': 23, 'rating': 83, 'nat': 'Brazil'},
            {'name': 'Dodo', 'pos': 'RB', 'age': 24, 'rating': 82, 'nat': 'Brazil'},
            {'name': 'Mykola Matviyenko', 'pos': 'CB', 'age': 26, 'rating': 81, 'nat': 'Ukraine'},
            {'name': 'Taras Stepanenko', 'pos': 'CDM', 'age': 33, 'rating': 82, 'nat': 'Ukraine'},
            {'name': 'Alan Patrick', 'pos': 'CM', 'age': 30, 'rating': 81, 'nat': 'Brazil'},
            {'name': 'Marcos Antônio', 'pos': 'CM', 'age': 23, 'rating': 83, 'nat': 'Brazil'},
            {'name': 'Fernando', 'pos': 'CB', 'age': 28, 'rating': 80, 'nat': 'Brazil'},
            {'name': 'David Neres', 'pos': 'RW', 'age': 26, 'rating': 84, 'nat': 'Brazil'},
            {'name': 'Pyatov', 'pos': 'GK', 'age': 38, 'rating': 82, 'nat': 'Ukraine'},
        ]
    },

    # --- Switzerland ---
    'young_boys': {
        'name': 'Young Boys',
        'country': 'Switzerland',
        'league': 'Champions League',
        'players': [
            {'name': 'David von Ballmoos', 'pos': 'GK', 'age': 28, 'rating': 82, 'nat': 'Switzerland'},
            {'name': 'Anthony Racioppi', 'pos': 'GK', 'age': 26, 'rating': 80, 'nat': 'Switzerland'},
            {'name': 'Silvan Hefti', 'pos': 'RB', 'age': 24, 'rating': 81, 'nat': 'Switzerland'},
            {'name': 'Jordan Lotomba', 'pos': 'RB', 'age': 24, 'rating': 82, 'nat': 'Switzerland'},
            {'name': 'Gonçalo Cardoso', 'pos': 'CB', 'age': 23, 'rating': 79, 'nat': 'Portugal'},
            {'name': 'Christian Fassnacht', 'pos': 'RW', 'age': 27, 'rating': 83, 'nat': 'Switzerland'},
            {'name': 'Jordan Siebatcheu', 'pos': 'ST', 'age': 26, 'rating': 82, 'nat': 'USA'},
            {'name': 'Christopher Martins', 'pos': 'CM', 'age': 26, 'rating': 81, 'nat': 'Luxembourg'},
            {'name': 'Fabian Lustenberger', 'pos': 'CDM', 'age': 36, 'rating': 80, 'nat': 'Switzerland'},
            {'name': 'Ramy Bensebaini', 'pos': 'LB', 'age': 28, 'rating': 82, 'nat': 'Algeria'},
            {'name': 'Theoson Jordan Siebatcheu', 'pos': 'ST', 'age': 26, 'rating': 82, 'nat': 'USA'},
        ]
    },

    # --- Serbia ---
    'red_star_belgrade': {
        'name': 'Red Star Belgrade',
        'country': 'Serbia',
        'league': 'Champions League',
        'players': [
            {'name': 'Milan Borjan', 'pos': 'GK', 'age': 35, 'rating': 83, 'nat': 'Canada'},
            {'name': 'Vladimir Stojković', 'pos': 'GK', 'age': 39, 'rating': 81, 'nat': 'Serbia'},
            {'name': 'Miloš Degenek', 'pos': 'CB', 'age': 29, 'rating': 82, 'nat': 'Australia'},
            {'name': 'Naby Sarr', 'pos': 'CB', 'age': 28, 'rating': 81, 'nat': 'France'},
            {'name': 'Guelor Kanga', 'pos': 'CM', 'age': 31, 'rating': 80, 'nat': 'Gabon'},
            {'name': 'Srđan Babić', 'pos': 'CB', 'age': 27, 'rating': 79, 'nat': 'Serbia'},
            {'name': 'Richairo Živković', 'pos': 'ST', 'age': 26, 'rating': 81, 'nat': 'Netherlands'},
            {'name': 'Aleksandar Katai', 'pos': 'RW', 'age': 31, 'rating': 82, 'nat': 'Serbia'},
            {'name': 'Nemanja Milunović', 'pos': 'CB', 'age': 33, 'rating': 80, 'nat': 'Serbia'},
            {'name': 'Miloš Degenek', 'pos': 'CB', 'age': 29, 'rating': 82, 'nat': 'Australia'},
            {'name': 'El Fardou Ben Nabouhane', 'pos': 'LW', 'age': 34, 'rating': 80, 'nat': 'Comoros'},
        ]
    },

})

# -------------------
# Europa League 2024 (Spain)
# -------------------

TEAM_ROSTERS.update({

    'real_sociedad': {
        'name': 'Real Sociedad',
        'country': 'Spain',
        'league': 'Europa League',
        'players': [
            {'name': 'Álex Remiro', 'pos': 'GK', 'age': 28, 'rating': 82, 'nat': 'Spain'},
            {'name': 'Mathew Ryan', 'pos': 'GK', 'age': 32, 'rating': 80, 'nat': 'Australia'},
            {'name': 'Robin Le Normand', 'pos': 'CB', 'age': 27, 'rating': 84, 'nat': 'France'},
            {'name': 'Aritz Elustondo', 'pos': 'CB', 'age': 30, 'rating': 82, 'nat': 'Spain'},
            {'name': 'Joseba Zaldua', 'pos': 'RB', 'age': 29, 'rating': 81, 'nat': 'Spain'},
            {'name': 'Joseba Zaldúa', 'pos': 'RB', 'age': 29, 'rating': 81, 'nat': 'Spain'},
            {'name': 'Mikel Merino', 'pos': 'CM', 'age': 26, 'rating': 84, 'nat': 'Spain'},
            {'name': 'Martin Zubimendi', 'pos': 'CDM', 'age': 23, 'rating': 82, 'nat': 'Spain'},
            {'name': 'Mikel Oyarzabal', 'pos': 'LW', 'age': 26, 'rating': 86, 'nat': 'Spain'},
            {'name': 'Alexander Isak', 'pos': 'ST', 'age': 24, 'rating': 85, 'nat': 'Sweden'},
            {'name': 'Carlos Fernández', 'pos': 'ST', 'age': 26, 'rating': 81, 'nat': 'Spain'},
        ]
    },

    'villarreal': {
        'name': 'Villarreal',
        'country': 'Spain',
        'league': 'Europa League',
        'players': [
            {'name': 'Gerónimo Rulli', 'pos': 'GK', 'age': 31, 'rating': 82, 'nat': 'Argentina'},
            {'name': 'Sergio Asenjo', 'pos': 'GK', 'age': 35, 'rating': 80, 'nat': 'Spain'},
            {'name': 'Pau Torres', 'pos': 'CB', 'age': 25, 'rating': 85, 'nat': 'Spain'},
            {'name': 'Raúl Albiol', 'pos': 'CB', 'age': 38, 'rating': 81, 'nat': 'Spain'},
            {'name': 'Juan Foyth', 'pos': 'CB', 'age': 25, 'rating': 82, 'nat': 'Argentina'},
            {'name': 'Mario Gaspar', 'pos': 'RB', 'age': 32, 'rating': 81, 'nat': 'Spain'},
            {'name': 'Étienne Capoue', 'pos': 'CDM', 'age': 34, 'rating': 83, 'nat': 'France'},
            {'name': 'Manu Trigueros', 'pos': 'CM', 'age': 32, 'rating': 82, 'nat': 'Spain'},
            {'name': 'Arnaut Danjuma', 'pos': 'LW', 'age': 26, 'rating': 84, 'nat': 'Netherlands'},
            {'name': 'Boulaye Dia', 'pos': 'ST', 'age': 26, 'rating': 82, 'nat': 'Senegal'},
            {'name': 'Samuel Chukwueze', 'pos': 'RW', 'age': 25, 'rating': 83, 'nat': 'Nigeria'},
        ]
    },

    'real_betis': {
        'name': 'Real Betis',
        'country': 'Spain',
        'league': 'Europa League',
        'players': [
            {'name': 'Rui Silva', 'pos': 'GK', 'age': 30, 'rating': 83, 'nat': 'Portugal'},
            {'name': 'Claudio Bravo', 'pos': 'GK', 'age': 41, 'rating': 81, 'nat': 'Chile'},
            {'name': 'Marc Bartra', 'pos': 'CB', 'age': 32, 'rating': 82, 'nat': 'Spain'},
            {'name': 'Germán Pezzella', 'pos': 'CB', 'age': 32, 'rating': 81, 'nat': 'Argentina'},
            {'name': 'Emerson Royal', 'pos': 'RB', 'age': 24, 'rating': 82, 'nat': 'Brazil'},
            {'name': 'Alex Moreno', 'pos': 'LB', 'age': 31, 'rating': 81, 'nat': 'Spain'},
            {'name': 'Guido Rodríguez', 'pos': 'CDM', 'age': 28, 'rating': 84, 'nat': 'Argentina'},
            {'name': 'Nabil Fekir', 'pos': 'CAM', 'age': 30, 'rating': 85, 'nat': 'France'},
            {'name': 'Juanmi', 'pos': 'ST', 'age': 28, 'rating': 82, 'nat': 'Spain'},
            {'name': 'Borja Iglesias', 'pos': 'ST', 'age': 28, 'rating': 83, 'nat': 'Spain'},
            {'name': 'Sergio Canales', 'pos': 'CM', 'age': 31, 'rating': 84, 'nat': 'Spain'},
        ]
    },

    'athletic_bilbao': {
        'name': 'Athletic Bilbao',
        'country': 'Spain',
        'league': 'Europa League',
        'players': [
            {'name': 'Unai Simón', 'pos': 'GK', 'age': 26, 'rating': 85, 'nat': 'Spain'},
            {'name': 'Julen Agirrezabala', 'pos': 'GK', 'age': 22, 'rating': 79, 'nat': 'Spain'},
            {'name': 'Iñigo Martínez', 'pos': 'CB', 'age': 33, 'rating': 83, 'nat': 'Spain'},
            {'name': 'Yeray Álvarez', 'pos': 'CB', 'age': 30, 'rating': 82, 'nat': 'Spain'},
            {'name': 'Óscar de Marcos', 'pos': 'RB', 'age': 34, 'rating': 81, 'nat': 'Spain'},
            {'name': 'Ander Capa', 'pos': 'RB', 'age': 30, 'rating': 80, 'nat': 'Spain'},
            {'name': 'Mikel Vesga', 'pos': 'CM', 'age': 28, 'rating': 81, 'nat': 'Spain'},
            {'name': 'Mikel San José', 'pos': 'CDM', 'age': 34, 'rating': 80, 'nat': 'Spain'},
            {'name': 'Iker Muniain', 'pos': 'LW', 'age': 30, 'rating': 84, 'nat': 'Spain'},
            {'name': 'Raúl García', 'pos': 'CAM', 'age': 36, 'rating': 82, 'nat': 'Spain'},
            {'name': 'Nico Williams', 'pos': 'RW', 'age': 21, 'rating': 81, 'nat': 'Spain'},
        ]
    },

})

# -------------------
# Europa League 2024 (Germany)
# -------------------

TEAM_ROSTERS.update({

    'eintracht_frankfurt': {
        'name': 'Eintracht Frankfurt',
        'country': 'Germany',
        'league': 'Europa League',
        'players': [
            {'name': 'Kevin Trapp', 'pos': 'GK', 'age': 33, 'rating': 84, 'nat': 'Germany'},
            {'name': 'Rúnar Alex Rúnarsson', 'pos': 'GK', 'age': 27, 'rating': 80, 'nat': 'Iceland'},
            {'name': 'Martin Hinteregger', 'pos': 'CB', 'age': 31, 'rating': 82, 'nat': 'Austria'},
            {'name': 'Tuta', 'pos': 'CB', 'age': 26, 'rating': 81, 'nat': 'Brazil'},
            {'name': 'Almamy Touré', 'pos': 'RB', 'age': 27, 'rating': 80, 'nat': 'France'},
            {'name': 'Jesper Lindstrøm', 'pos': 'RW', 'age': 23, 'rating': 84, 'nat': 'Denmark'},
            {'name': 'Filip Kostić', 'pos': 'LW', 'age': 31, 'rating': 85, 'nat': 'Serbia'},
            {'name': 'Djibril Sow', 'pos': 'CM', 'age': 25, 'rating': 82, 'nat': 'Switzerland'},
            {'name': 'Kristijan Jakić', 'pos': 'CDM', 'age': 25, 'rating': 81, 'nat': 'Croatia'},
            {'name': 'Rafael Borré', 'pos': 'ST', 'age': 27, 'rating': 82, 'nat': 'Colombia'},
            {'name': 'Gonçalo Paciência', 'pos': 'ST', 'age': 27, 'rating': 80, 'nat': 'Portugal'},
        ]
    },

    'union_berlin': {
        'name': 'Union Berlin',
        'country': 'Germany',
        'league': 'Europa League',
        'players': [
            {'name': 'Rafal Gikiewicz', 'pos': 'GK', 'age': 35, 'rating': 80, 'nat': 'Poland'},
            {'name': 'Loris Karius', 'pos': 'GK', 'age': 31, 'rating': 79, 'nat': 'Germany'},
            {'name': 'Robin Knoche', 'pos': 'CB', 'age': 31, 'rating': 81, 'nat': 'Germany'},
            {'name': 'Paul Jaeckel', 'pos': 'CB', 'age': 24, 'rating': 79, 'nat': 'Germany'},
            {'name': 'Andreas Luthe', 'pos': 'GK', 'age': 35, 'rating': 78, 'nat': 'Germany'},
            {'name': 'Christopher Trimmel', 'pos': 'RB', 'age': 36, 'rating': 81, 'nat': 'Austria'},
            {'name': 'Grischa Prömel', 'pos': 'CM', 'age': 28, 'rating': 82, 'nat': 'Germany'},
            {'name': 'Julian Ryerson', 'pos': 'RB', 'age': 26, 'rating': 81, 'nat': 'Norway'},
            {'name': 'Sheraldo Becker', 'pos': 'RW', 'age': 27, 'rating': 82, 'nat': 'Suriname'},
            {'name': 'Taiwo Awoniyi', 'pos': 'ST', 'age': 25, 'rating': 83, 'nat': 'Nigeria'},
            {'name': 'Max Kruse', 'pos': 'ST', 'age': 36, 'rating': 81, 'nat': 'Germany'},
        ]
    },

    'freiburg': {
        'name': 'Freiburg',
        'country': 'Germany',
        'league': 'Europa League',
        'players': [
            {'name': 'Mark Flekken', 'pos': 'GK', 'age': 29, 'rating': 82, 'nat': 'Netherlands'},
            {'name': 'Christian Früchtl', 'pos': 'GK', 'age': 23, 'rating': 77, 'nat': 'Germany'},
            {'name': 'Nico Schlotterbeck', 'pos': 'CB', 'age': 24, 'rating': 84, 'nat': 'Germany'},
            {'name': 'Keven Schlotterbeck', 'pos': 'CB', 'age': 26, 'rating': 82, 'nat': 'Germany'},
            {'name': 'Luca Itter', 'pos': 'RB', 'age': 24, 'rating': 79, 'nat': 'Germany'},
            {'name': 'Christian Günter', 'pos': 'LB', 'age': 30, 'rating': 83, 'nat': 'Germany'},
            {'name': 'Vincenzo Grifo', 'pos': 'CAM', 'age': 29, 'rating': 84, 'nat': 'Italy'},
            {'name': 'Manuel Gulde', 'pos': 'CB', 'age': 31, 'rating': 81, 'nat': 'Germany'},
            {'name': 'Lucas Höler', 'pos': 'ST', 'age': 28, 'rating': 82, 'nat': 'Germany'},
            {'name': 'Roland Sallai', 'pos': 'LW', 'age': 25, 'rating': 83, 'nat': 'Hungary'},
            {'name': 'Yannik Keitel', 'pos': 'CM', 'age': 21, 'rating': 79, 'nat': 'Germany'},
        ]
    },

    'hoffenheim': {
        'name': 'Hoffenheim',
        'country': 'Germany',
        'league': 'Europa League',
        'players': [
            {'name': 'Oliver Baumann', 'pos': 'GK', 'age': 33, 'rating': 83, 'nat': 'Germany'},
            {'name': 'Philipp Pentke', 'pos': 'GK', 'age': 38, 'rating': 78, 'nat': 'Germany'},
            {'name': 'Kevin Akpoguma', 'pos': 'CB', 'age': 27, 'rating': 81, 'nat': 'Germany'},
            {'name': 'Pavel Kadeřábek', 'pos': 'RB', 'age': 31, 'rating': 81, 'nat': 'Czech Republic'},
            {'name': 'Chris Richards', 'pos': 'CB', 'age': 24, 'rating': 80, 'nat': 'USA'},
            {'name': 'Diadie Samassékou', 'pos': 'CDM', 'age': 26, 'rating': 82, 'nat': 'Mali'},
            {'name': 'Florian Grillitsch', 'pos': 'CM', 'age': 27, 'rating': 83, 'nat': 'Austria'},
            {'name': 'Andrej Kramarić', 'pos': 'ST', 'age': 32, 'rating': 84, 'nat': 'Croatia'},
            {'name': 'Munas Dabbur', 'pos': 'ST', 'age': 31, 'rating': 82, 'nat': 'Israel'},
            {'name': 'Ihlas Bebou', 'pos': 'RW', 'age': 28, 'rating': 82, 'nat': 'Togo'},
            {'name': 'Robert Skov', 'pos': 'LW', 'age': 26, 'rating': 83, 'nat': 'Denmark'},
        ]
    },

})

# -------------------
# Europa League 2024 (Italy)
# -------------------

TEAM_ROSTERS.update({

    'as_roma': {
        'name': 'AS Roma',
        'country': 'Italy',
        'league': 'Europa League',
        'players': [
            {'name': 'Rui Patricio', 'pos': 'GK', 'age': 36, 'rating': 84, 'nat': 'Portugal'},
            {'name': 'Marash Kumbulla', 'pos': 'CB', 'age': 23, 'rating': 81, 'nat': 'Albania'},
            {'name': 'Gianluca Mancini', 'pos': 'CB', 'age': 26, 'rating': 83, 'nat': 'Italy'},
            {'name': 'Chris Smalling', 'pos': 'CB', 'age': 34, 'rating': 82, 'nat': 'England'},
            {'name': 'Rick Karsdorp', 'pos': 'RB', 'age': 27, 'rating': 82, 'nat': 'Netherlands'},
            {'name': 'Nicolo Zaniolo', 'pos': 'CAM', 'age': 24, 'rating': 85, 'nat': 'Italy'},
            {'name': 'Lorenzo Pellegrini', 'pos': 'CM', 'age': 27, 'rating': 86, 'nat': 'Italy'},
            {'name': 'Henrikh Mkhitaryan', 'pos': 'CAM', 'age': 35, 'rating': 83, 'nat': 'Armenia'},
            {'name': 'Paulo Dybala', 'pos': 'ST', 'age': 30, 'rating': 87, 'nat': 'Argentina'},
            {'name': 'Tammy Abraham', 'pos': 'ST', 'age': 25, 'rating': 84, 'nat': 'England'},
            {'name': 'Nicolo Zaniolo', 'pos': 'RW', 'age': 24, 'rating': 85, 'nat': 'Italy'},
        ]
    },

    'lazio': {
        'name': 'Lazio',
        'country': 'Italy',
        'league': 'Europa League',
        'players': [
            {'name': 'Ivan Provedel', 'pos': 'GK', 'age': 29, 'rating': 82, 'nat': 'Italy'},
            {'name': 'Thomas Strakosha', 'pos': 'GK', 'age': 28, 'rating': 81, 'nat': 'Albania'},
            {'name': 'Francesco Acerbi', 'pos': 'CB', 'age': 35, 'rating': 84, 'nat': 'Italy'},
            {'name': 'Patric', 'pos': 'CB', 'age': 31, 'rating': 81, 'nat': 'Spain'},
            {'name': 'Manuel Lazzari', 'pos': 'RB', 'age': 29, 'rating': 82, 'nat': 'Italy'},
            {'name': 'Danilo Cataldi', 'pos': 'CM', 'age': 27, 'rating': 81, 'nat': 'Italy'},
            {'name': 'Sergej Milinković-Savić', 'pos': 'CM', 'age': 27, 'rating': 87, 'nat': 'Serbia'},
            {'name': 'Luis Alberto', 'pos': 'CAM', 'age': 30, 'rating': 85, 'nat': 'Spain'},
            {'name': 'Ciro Immobile', 'pos': 'ST', 'age': 33, 'rating': 88, 'nat': 'Italy'},
            {'name': 'Pedro', 'pos': 'RW', 'age': 36, 'rating': 83, 'nat': 'Spain'},
            {'name': 'Mattia Zaccagni', 'pos': 'LW', 'age': 27, 'rating': 84, 'nat': 'Italy'},
        ]
    },

    'atalanta': {
        'name': 'Atalanta',
        'country': 'Italy',
        'league': 'Europa League',
        'players': [
            {'name': 'Juan Musso', 'pos': 'GK', 'age': 26, 'rating': 83, 'nat': 'Argentina'},
            {'name': 'Pierluigi Gollini', 'pos': 'GK', 'age': 27, 'rating': 81, 'nat': 'Italy'},
            {'name': 'José Luis Palomino', 'pos': 'CB', 'age': 32, 'rating': 81, 'nat': 'Argentina'},
            {'name': 'Merih Demiral', 'pos': 'CB', 'age': 25, 'rating': 83, 'nat': 'Turkey'},
            {'name': 'Hans Hateboer', 'pos': 'RB', 'age': 27, 'rating': 82, 'nat': 'Netherlands'},
            {'name': 'Teun Koopmeiners', 'pos': 'CM', 'age': 25, 'rating': 85, 'nat': 'Netherlands'},
            {'name': 'Ruslan Malinovskyi', 'pos': 'CAM', 'age': 28, 'rating': 84, 'nat': 'Ukraine'},
            {'name': 'Berat Djimsiti', 'pos': 'CB', 'age': 29, 'rating': 81, 'nat': 'Albania'},
            {'name': 'Duván Zapata', 'pos': 'ST', 'age': 31, 'rating': 85, 'nat': 'Colombia'},
            {'name': 'Luis Muriel', 'pos': 'ST', 'age': 31, 'rating': 84, 'nat': 'Colombia'},
            {'name': 'Josip Iličić', 'pos': 'CAM', 'age': 35, 'rating': 83, 'nat': 'Slovenia'},
        ]
    },

    'fiorentina': {
        'name': 'Fiorentina',
        'country': 'Italy',
        'league': 'Europa League',
        'players': [
            {'name': 'Bartłomiej Drągowski', 'pos': 'GK', 'age': 26, 'rating': 82, 'nat': 'Poland'},
            {'name': 'Alfredo Donnarumma', 'pos': 'GK', 'age': 29, 'rating': 80, 'nat': 'Italy'},
            {'name': 'Nikola Milenković', 'pos': 'CB', 'age': 25, 'rating': 84, 'nat': 'Serbia'},
            {'name': 'Igor', 'pos': 'CB', 'age': 28, 'rating': 82, 'nat': 'Brazil'},
            {'name': 'Cristiano Biraghi', 'pos': 'LB', 'age': 30, 'rating': 82, 'nat': 'Italy'},
            {'name': 'Giacomo Bonaventura', 'pos': 'CM', 'age': 34, 'rating': 81, 'nat': 'Italy'},
            {'name': 'Nicolò González', 'pos': 'RW', 'age': 23, 'rating': 83, 'nat': 'Argentina'},
            {'name': 'Arthur Cabral', 'pos': 'ST', 'age': 25, 'rating': 84, 'nat': 'Brazil'},
            {'name': 'Riccardo Saponara', 'pos': 'CAM', 'age': 32, 'rating': 81, 'nat': 'Italy'},
            {'name': 'Giacomo Bonaventura', 'pos': 'CM', 'age': 34, 'rating': 81, 'nat': 'Italy'},
            {'name': 'Christian Kouamé', 'pos': 'LW', 'age': 26, 'rating': 82, 'nat': 'Ivory Coast'},
        ]
    },

})

# -------------------
# Europa League 2024 (France)
# -------------------

TEAM_ROSTERS.update({

    'lille': {
        'name': 'Lille',
        'country': 'France',
        'league': 'Europa League',
        'players': [
            {'name': 'Illan Meslier', 'pos': 'GK', 'age': 24, 'rating': 83, 'nat': 'France'},
            {'name': 'Léo Jardim', 'pos': 'GK', 'age': 25, 'rating': 79, 'nat': 'Brazil'},
            {'name': 'José Fonte', 'pos': 'CB', 'age': 40, 'rating': 81, 'nat': 'Portugal'},
            {'name': 'Sven Botman', 'pos': 'CB', 'age': 24, 'rating': 84, 'nat': 'Netherlands'},
            {'name': 'Reinildo Mandava', 'pos': 'LB', 'age': 28, 'rating': 82, 'nat': 'Mozambique'},
            {'name': 'Timothy Weah', 'pos': 'RW', 'age': 23, 'rating': 82, 'nat': 'USA'},
            {'name': 'Benjamin André', 'pos': 'CDM', 'age': 33, 'rating': 83, 'nat': 'France'},
            {'name': 'Xeka', 'pos': 'CM', 'age': 29, 'rating': 82, 'nat': 'Portugal'},
            {'name': 'Jonathan David', 'pos': 'ST', 'age': 23, 'rating': 86, 'nat': 'Canada'},
            {'name': 'Angel Gomes', 'pos': 'CAM', 'age': 21, 'rating': 81, 'nat': 'England'},
            {'name': 'Jonathan Ikoné', 'pos': 'LW', 'age': 25, 'rating': 84, 'nat': 'France'},
        ]
    },

    'nice': {
        'name': 'Nice',
        'country': 'France',
        'league': 'Europa League',
        'players': [
            {'name': 'Walter Benítez', 'pos': 'GK', 'age': 28, 'rating': 82, 'nat': 'Argentina'},
            {'name': 'Marcin Bulka', 'pos': 'GK', 'age': 23, 'rating': 78, 'nat': 'Poland'},
            {'name': 'Justin Kluivert', 'pos': 'RW', 'age': 24, 'rating': 83, 'nat': 'Netherlands'},
            {'name': 'Jean-Clair Todibo', 'pos': 'CB', 'age': 23, 'rating': 82, 'nat': 'France'},
            {'name': 'Dante', 'pos': 'CB', 'age': 39, 'rating': 80, 'nat': 'Brazil'},
            {'name': 'Youcef Atal', 'pos': 'RB', 'age': 26, 'rating': 83, 'nat': 'Algeria'},
            {'name': 'Aaron Ramsey', 'pos': 'CM', 'age': 33, 'rating': 81, 'nat': 'Wales'},
            {'name': 'Wylan Cyprien', 'pos': 'CM', 'age': 27, 'rating': 81, 'nat': 'France'},
            {'name': 'Amine Gouiri', 'pos': 'ST', 'age': 23, 'rating': 84, 'nat': 'France'},
            {'name': 'Kasper Dolberg', 'pos': 'ST', 'age': 25, 'rating': 83, 'nat': 'Denmark'},
            {'name': 'Rony Lopes', 'pos': 'LW', 'age': 27, 'rating': 82, 'nat': 'Portugal'},
        ]
    },

    'rennes': {
        'name': 'Rennes',
        'country': 'France',
        'league': 'Europa League',
        'players': [
            {'name': 'Alban Lafont', 'pos': 'GK', 'age': 25, 'rating': 84, 'nat': 'France'},
            {'name': 'Kemen', 'pos': 'CB', 'age': 25, 'rating': 80, 'nat': 'France'},
            {'name': 'Lovro Majer', 'pos': 'CAM', 'age': 24, 'rating': 84, 'nat': 'Croatia'},
            {'name': 'Dalbert', 'pos': 'LB', 'age': 29, 'rating': 81, 'nat': 'Brazil'},
            {'name': 'Hamari Traoré', 'pos': 'RB', 'age': 31, 'rating': 82, 'nat': 'Mali'},
            {'name': 'Benjamin Bourigeaud', 'pos': 'CM', 'age': 28, 'rating': 83, 'nat': 'France'},
            {'name': 'Faitout Maouassa', 'pos': 'LB', 'age': 25, 'rating': 81, 'nat': 'France'},
            {'name': 'Gaëtan Laborde', 'pos': 'ST', 'age': 28, 'rating': 83, 'nat': 'France'},
            {'name': 'Amine Gouiri', 'pos': 'RW', 'age': 23, 'rating': 84, 'nat': 'France'},
            {'name': 'Martin Terrier', 'pos': 'LW', 'age': 25, 'rating': 82, 'nat': 'France'},
            {'name': 'Toma Basic', 'pos': 'CM', 'age': 28, 'rating': 81, 'nat': 'Croatia'},
        ]
    },

    'lens': {
        'name': 'Lens',
        'country': 'France',
        'league': 'Europa League',
        'players': [
            {'name': 'Brice Samba', 'pos': 'GK', 'age': 29, 'rating': 82, 'nat': 'DR Congo'},
            {'name': 'Wuilker Faríñez', 'pos': 'GK', 'age': 25, 'rating': 80, 'nat': 'Venezuela'},
            {'name': 'Jonathan Clauss', 'pos': 'RB', 'age': 30, 'rating': 84, 'nat': 'France'},
            {'name': 'Seko Fofana', 'pos': 'CM', 'age': 27, 'rating': 85, 'nat': 'Ivory Coast'},
            {'name': 'Joseph Lopy', 'pos': 'CM', 'age': 27, 'rating': 81, 'nat': 'Senegal'},
            {'name': 'Przemysław Frankowski', 'pos': 'RW', 'age': 27, 'rating': 82, 'nat': 'Poland'},
            {'name': 'Cheick Doucouré', 'pos': 'CDM', 'age': 22, 'rating': 83, 'nat': 'Mali'},
            {'name': 'Fodé Ballo-Touré', 'pos': 'LB', 'age': 26, 'rating': 82, 'nat': 'France'},
            {'name': 'Gaël Kakuta', 'pos': 'CAM', 'age': 32, 'rating': 81, 'nat': 'DR Congo'},
            {'name': 'Przemysław Frankowski', 'pos': 'RW', 'age': 27, 'rating': 82, 'nat': 'Poland'},
            {'name': 'Ignatius Ganago', 'pos': 'ST', 'age': 24, 'rating': 81, 'nat': 'Cameroon'},
        ]
    },

})

# -------------------
# Europa League 2024 (Portugal)
# -------------------

TEAM_ROSTERS.update({

    'braga': {
        'name': 'Braga',
        'country': 'Portugal',
        'league': 'Europa League',
        'players': [
            {'name': 'Matheus', 'pos': 'GK', 'age': 25, 'rating': 82, 'nat': 'Brazil'},
            {'name': 'Carlos Hita', 'pos': 'GK', 'age': 27, 'rating': 79, 'nat': 'Spain'},
            {'name': 'David Carmo', 'pos': 'CB', 'age': 23, 'rating': 83, 'nat': 'Portugal'},
            {'name': 'Paulo Oliveira', 'pos': 'CB', 'age': 30, 'rating': 82, 'nat': 'Portugal'},
            {'name': 'Paulinho', 'pos': 'RB', 'age': 26, 'rating': 81, 'nat': 'Portugal'},
            {'name': 'Fransergio', 'pos': 'CM', 'age': 30, 'rating': 82, 'nat': 'Brazil'},
            {'name': 'Ricardo Esgaio', 'pos': 'RB', 'age': 29, 'rating': 81, 'nat': 'Portugal'},
            {'name': 'Iuri Medeiros', 'pos': 'LW', 'age': 28, 'rating': 82, 'nat': 'Portugal'},
            {'name': 'André Horta', 'pos': 'CAM', 'age': 26, 'rating': 81, 'nat': 'Portugal'},
            {'name': 'Arthur Gomes', 'pos': 'RW', 'age': 26, 'rating': 82, 'nat': 'Brazil'},
            {'name': 'Paulinho', 'pos': 'ST', 'age': 25, 'rating': 81, 'nat': 'Brazil'},
        ]
    },

    'vitoria_guimaraes': {
        'name': 'Vitória Guimarães',
        'country': 'Portugal',
        'league': 'Europa League',
        'players': [
            {'name': 'Paulo Lopes', 'pos': 'GK', 'age': 35, 'rating': 79, 'nat': 'Portugal'},
            {'name': 'André Moreira', 'pos': 'GK', 'age': 27, 'rating': 80, 'nat': 'Portugal'},
            {'name': 'Fábio Cardoso', 'pos': 'CB', 'age': 30, 'rating': 82, 'nat': 'Portugal'},
            {'name': 'David Tavares', 'pos': 'CB', 'age': 24, 'rating': 81, 'nat': 'Portugal'},
            {'name': 'Miguel Loureiro', 'pos': 'RB', 'age': 24, 'rating': 80, 'nat': 'Portugal'},
            {'name': 'Ricardo Esgaio', 'pos': 'RB', 'age': 29, 'rating': 81, 'nat': 'Portugal'},
            {'name': 'João Moutinho', 'pos': 'CM', 'age': 37, 'rating': 84, 'nat': 'Portugal'},
            {'name': 'Fran Navarro', 'pos': 'ST', 'age': 24, 'rating': 81, 'nat': 'Spain'},
            {'name': 'Samuel Lino', 'pos': 'LW', 'age': 23, 'rating': 82, 'nat': 'Brazil'},
            {'name': 'Ricardo Valente', 'pos': 'RW', 'age': 28, 'rating': 80, 'nat': 'Portugal'},
            {'name': 'Mamadou Loum', 'pos': 'CDM', 'age': 25, 'rating': 81, 'nat': 'Senegal'},
        ]
    },

    'rio_ave': {
        'name': 'Rio Ave',
        'country': 'Portugal',
        'league': 'Europa League',
        'players': [
            {'name': 'Ivan Zlobin', 'pos': 'GK', 'age': 27, 'rating': 80, 'nat': 'Russia'},
            {'name': 'Cláudio Ramos', 'pos': 'GK', 'age': 33, 'rating': 81, 'nat': 'Portugal'},
            {'name': 'Lucas Piazon', 'pos': 'RW', 'age': 27, 'rating': 81, 'nat': 'Brazil'},
            {'name': 'Luka Ilić', 'pos': 'CM', 'age': 23, 'rating': 80, 'nat': 'Serbia'},
            {'name': 'Danielson', 'pos': 'CB', 'age': 28, 'rating': 81, 'nat': 'Brazil'},
            {'name': 'Gil Dias', 'pos': 'LW', 'age': 27, 'rating': 81, 'nat': 'Portugal'},
            {'name': 'Anderson', 'pos': 'CDM', 'age': 26, 'rating': 80, 'nat': 'Brazil'},
            {'name': 'Fábio Cardoso', 'pos': 'CB', 'age': 30, 'rating': 81, 'nat': 'Portugal'},
            {'name': 'Tiago Rodrigues', 'pos': 'CM', 'age': 30, 'rating': 80, 'nat': 'Portugal'},
            {'name': 'Pedro Amaral', 'pos': 'LB', 'age': 26, 'rating': 80, 'nat': 'Portugal'},
            {'name': 'Diego Lopes', 'pos': 'ST', 'age': 30, 'rating': 81, 'nat': 'Brazil'},
        ]
    },

})

# -------------------
# Europa League 2024 (Netherlands)
# -------------------

TEAM_ROSTERS.update({

    'az_alkmaar': {
        'name': 'AZ Alkmaar',
        'country': 'Netherlands',
        'league': 'Europa League',
        'players': [
            {'name': 'Rene Hake', 'pos': 'GK', 'age': 25, 'rating': 81, 'nat': 'Netherlands'},
            {'name': 'Pablo Rosario', 'pos': 'CM', 'age': 25, 'rating': 82, 'nat': 'Netherlands'},
            {'name': 'Owen Wijndal', 'pos': 'LB', 'age': 22, 'rating': 83, 'nat': 'Netherlands'},
            {'name': 'Teun Koopmeiners', 'pos': 'CDM', 'age': 25, 'rating': 85, 'nat': 'Netherlands'},
            {'name': 'Vangelis Pavlidis', 'pos': 'ST', 'age': 24, 'rating': 83, 'nat': 'Greece'},
            {'name': 'Albert Guðmundsson', 'pos': 'RW', 'age': 23, 'rating': 82, 'nat': 'Iceland'},
            {'name': 'Jesper Karlsson', 'pos': 'LW', 'age': 24, 'rating': 84, 'nat': 'Sweden'},
            {'name': 'Ibrahim Sangaré', 'pos': 'CM', 'age': 25, 'rating': 84, 'nat': 'Ivory Coast'},
            {'name': 'Owen Wijndal', 'pos': 'LB', 'age': 22, 'rating': 83, 'nat': 'Netherlands'},
            {'name': 'Ramon Hendriks', 'pos': 'CB', 'age': 23, 'rating': 81, 'nat': 'Netherlands'},
            {'name': 'Rasmus Lauritsen', 'pos': 'CB', 'age': 27, 'rating': 82, 'nat': 'Denmark'},
        ]
    },

    'fc_twente': {
        'name': 'FC Twente',
        'country': 'Netherlands',
        'league': 'Europa League',
        'players': [
            {'name': 'Nick Marsman', 'pos': 'GK', 'age': 34, 'rating': 80, 'nat': 'Netherlands'},
            {'name': 'Mats Deijl', 'pos': 'RB', 'age': 26, 'rating': 81, 'nat': 'Netherlands'},
            {'name': 'Roemerato', 'pos': 'CB', 'age': 26, 'rating': 80, 'nat': 'Netherlands'},
            {'name': 'Vaclav Cerny', 'pos': 'RW', 'age': 25, 'rating': 82, 'nat': 'Netherlands'},
            {'name': 'Danilo', 'pos': 'LB', 'age': 23, 'rating': 81, 'nat': 'Brazil'},
            {'name': 'Danilo Pereira', 'pos': 'CDM', 'age': 28, 'rating': 82, 'nat': 'Portugal'},
            {'name': 'Danilo', 'pos': 'ST', 'age': 23, 'rating': 81, 'nat': 'Brazil'},
            {'name': 'Thijs Dallinga', 'pos': 'ST', 'age': 23, 'rating': 82, 'nat': 'Netherlands'},
            {'name': 'Navarone Foor', 'pos': 'CM', 'age': 31, 'rating': 80, 'nat': 'Netherlands'},
            {'name': 'Emmanuel Matuta', 'pos': 'CM', 'age': 21, 'rating': 79, 'nat': 'Belgium'},
            {'name': 'Wout Brama', 'pos': 'CB', 'age': 36, 'rating': 78, 'nat': 'Netherlands'},
        ]
    },

    'fc_utrecht': {
        'name': 'FC Utrecht',
        'country': 'Netherlands',
        'league': 'Europa League',
        'players': [
            {'name': 'Maarten Paes', 'pos': 'GK', 'age': 25, 'rating': 81, 'nat': 'Netherlands'},
            {'name': 'Joris Kramer', 'pos': 'CB', 'age': 27, 'rating': 80, 'nat': 'Netherlands'},
            {'name': 'Dalmau', 'pos': 'ST', 'age': 26, 'rating': 82, 'nat': 'Spain'},
            {'name': 'Hidde ter Avest', 'pos': 'RB', 'age': 24, 'rating': 81, 'nat': 'Netherlands'},
            {'name': 'Lassana Faye', 'pos': 'LB', 'age': 25, 'rating': 80, 'nat': 'Netherlands'},
            {'name': 'Simon Gustafson', 'pos': 'CM', 'age': 28, 'rating': 82, 'nat': 'Sweden'},
            {'name': 'Rocco Robert Shein', 'pos': 'CM', 'age': 20, 'rating': 78, 'nat': 'Estonia'},
            {'name': 'Fran Sol', 'pos': 'ST', 'age': 30, 'rating': 81, 'nat': 'Spain'},
            {'name': 'Jean-Christophe Bahebeck', 'pos': 'RW', 'age': 28, 'rating': 81, 'nat': 'France'},
            {'name': 'Anastasios Douvikas', 'pos': 'ST', 'age': 23, 'rating': 82, 'nat': 'Greece'},
            {'name': 'Hidde ter Avest', 'pos': 'RB', 'age': 24, 'rating': 81, 'nat': 'Netherlands'},
        ]
    },

})

# -------------------
# Europa League 2024 (Belgium)
# -------------------

TEAM_ROSTERS.update({

    'genk': {
        'name': 'Genk',
        'country': 'Belgium',
        'league': 'Europa League',
        'players': [
            {'name': 'Maarten Vandevoordt', 'pos': 'GK', 'age': 21, 'rating': 82, 'nat': 'Belgium'},
            {'name': 'Mats Rits', 'pos': 'CM', 'age': 28, 'rating': 82, 'nat': 'Belgium'},
            {'name': 'Carlos Cuesta', 'pos': 'CB', 'age': 23, 'rating': 83, 'nat': 'Colombia'},
            {'name': 'Jhon Lucumí', 'pos': 'CB', 'age': 25, 'rating': 83, 'nat': 'Colombia'},
            {'name': 'Gerardo Arteaga', 'pos': 'LB', 'age': 23, 'rating': 82, 'nat': 'Mexico'},
            {'name': 'Moussa Sylla', 'pos': 'RW', 'age': 23, 'rating': 81, 'nat': 'France'},
            {'name': 'Theo Bongonda', 'pos': 'LW', 'age': 27, 'rating': 82, 'nat': 'Belgium'},
            {'name': 'Paul Onuachu', 'pos': 'ST', 'age': 28, 'rating': 84, 'nat': 'Nigeria'},
            {'name': 'Bryan Heynen', 'pos': 'CM', 'age': 27, 'rating': 83, 'nat': 'Belgium'},
            {'name': 'Sander Berge', 'pos': 'CDM', 'age': 25, 'rating': 84, 'nat': 'Norway'},
            {'name': 'Patrick Seck', 'pos': 'CB', 'age': 23, 'rating': 81, 'nat': 'Belgium'},
        ]
    },

    'royal_antwerp': {
        'name': 'Royal Antwerp',
        'country': 'Belgium',
        'league': 'Europa League',
        'players': [
            {'name': 'Jean Butez', 'pos': 'GK', 'age': 29, 'rating': 82, 'nat': 'France'},
            {'name': 'Sinan Bolat', 'pos': 'GK', 'age': 36, 'rating': 80, 'nat': 'Turkey'},
            {'name': 'Stefano Marzo', 'pos': 'RB', 'age': 30, 'rating': 81, 'nat': 'Belgium'},
            {'name': 'Dieumerci Mbokani', 'pos': 'ST', 'age': 37, 'rating': 80, 'nat': 'DR Congo'},
            {'name': 'Francois Moubandje', 'pos': 'LB', 'age': 32, 'rating': 80, 'nat': 'Switzerland'},
            {'name': 'Lior Refaelov', 'pos': 'CAM', 'age': 35, 'rating': 83, 'nat': 'Israel'},
            {'name': 'Raphael Holzhauser', 'pos': 'CM', 'age': 30, 'rating': 81, 'nat': 'Austria'},
            {'name': 'Vanderson', 'pos': 'CB', 'age': 23, 'rating': 82, 'nat': 'Brazil'},
            {'name': 'Diego Capel', 'pos': 'LW', 'age': 34, 'rating': 80, 'nat': 'Spain'},
            {'name': 'Radja Nainggolan', 'pos': 'CM', 'age': 36, 'rating': 82, 'nat': 'Belgium'},
            {'name': 'Michael Frey', 'pos': 'ST', 'age': 30, 'rating': 81, 'nat': 'Switzerland'},
        ]
    },

})

# -------------------
# Europa League 2024 (Greece)
# -------------------

TEAM_ROSTERS.update({

    'olympiacos': {
        'name': 'Olympiacos',
        'country': 'Greece',
        'league': 'Europa League',
        'players': [
            {'name': 'José Sá', 'pos': 'GK', 'age': 30, 'rating': 84, 'nat': 'Portugal'},
            {'name': 'Kostas Tsimikas', 'pos': 'LB', 'age': 27, 'rating': 83, 'nat': 'Greece'},
            {'name': 'Pape Abou Cissé', 'pos': 'CB', 'age': 28, 'rating': 82, 'nat': 'Senegal'},
            {'name': 'Bouchalakis', 'pos': 'CM', 'age': 28, 'rating': 81, 'nat': 'Greece'},
            {'name': 'Mady Camara', 'pos': 'CDM', 'age': 26, 'rating': 84, 'nat': 'Guinea'},
            {'name': 'Youssef El-Arabi', 'pos': 'ST', 'age': 36, 'rating': 83, 'nat': 'Morocco'},
            {'name': 'André Ayew', 'pos': 'LW', 'age': 33, 'rating': 82, 'nat': 'Ghana'},
            {'name': 'Valentin Rosier', 'pos': 'RB', 'age': 27, 'rating': 82, 'nat': 'France'},
            {'name': 'Giannoulis', 'pos': 'CB', 'age': 25, 'rating': 81, 'nat': 'Greece'},
            {'name': 'Cédric Bakambu', 'pos': 'ST', 'age': 33, 'rating': 84, 'nat': 'DR Congo'},
            {'name': 'Rony Lopes', 'pos': 'RW', 'age': 27, 'rating': 82, 'nat': 'Portugal'},
        ]
    },

    'panathinaikos': {
        'name': 'Panathinaikos',
        'country': 'Greece',
        'league': 'Europa League',
        'players': [
            {'name': 'Sokratis Dioudis', 'pos': 'GK', 'age': 28, 'rating': 82, 'nat': 'Greece'},
            {'name': 'François Moubandje', 'pos': 'LB', 'age': 32, 'rating': 80, 'nat': 'Switzerland'},
            {'name': 'Josip Mišić', 'pos': 'CM', 'age': 28, 'rating': 82, 'nat': 'Croatia'},
            {'name': 'Fran Varela', 'pos': 'RW', 'age': 24, 'rating': 80, 'nat': 'Spain'},
            {'name': 'Juan José Perea', 'pos': 'ST', 'age': 24, 'rating': 81, 'nat': 'Colombia'},
            {'name': 'Dimitrios Kolovos', 'pos': 'LW', 'age': 29, 'rating': 80, 'nat': 'Greece'},
            {'name': 'Jairo Riedewald', 'pos': 'CB', 'age': 25, 'rating': 81, 'nat': 'Netherlands'},
            {'name': 'Andraz Sporar', 'pos': 'ST', 'age': 28, 'rating': 81, 'nat': 'Slovenia'},
            {'name': 'Ioannis Kousoulos', 'pos': 'CB', 'age': 27, 'rating': 80, 'nat': 'Cyprus'},
            {'name': 'Vasilis Barkas', 'pos': 'GK', 'age': 28, 'rating': 81, 'nat': 'Greece'},
            {'name': 'Lazaros Christodoulopoulos', 'pos': 'CAM', 'age': 35, 'rating': 80, 'nat': 'Greece'},
        ]
    },

})

# -------------------
# Europa League 2024 (Czech Republic, Ukraine, Denmark, Norway, Israel, Cyprus)
# -------------------

TEAM_ROSTERS.update({

    'slavia_prague': {
        'name': 'Slavia Prague',
        'country': 'Czech Republic',
        'league': 'Europa League',
        'players': [
            {'name': 'Ondřej Kolář', 'pos': 'GK', 'age': 29, 'rating': 83, 'nat': 'Czech Republic'},
            {'name': 'Milan Škoda', 'pos': 'ST', 'age': 39, 'rating': 79, 'nat': 'Czech Republic'},
            {'name': 'David Hovorka', 'pos': 'CB', 'age': 29, 'rating': 81, 'nat': 'Czech Republic'},
            {'name': 'Peter Olayinka', 'pos': 'RW', 'age': 27, 'rating': 83, 'nat': 'Nigeria'},
            {'name': 'Lukas Masopust', 'pos': 'CM', 'age': 29, 'rating': 82, 'nat': 'Czech Republic'},
            {'name': 'Ewerton', 'pos': 'CB', 'age': 32, 'rating': 82, 'nat': 'Brazil'},
            {'name': 'Jan Boril', 'pos': 'LB', 'age': 28, 'rating': 81, 'nat': 'Czech Republic'},
            {'name': 'Lukáš Provod', 'pos': 'LW', 'age': 25, 'rating': 82, 'nat': 'Czech Republic'},
            {'name': 'Ondřej Lingr', 'pos': 'CAM', 'age': 25, 'rating': 81, 'nat': 'Czech Republic'},
            {'name': 'Simonas Stankevičius', 'pos': 'ST', 'age': 23, 'rating': 80, 'nat': 'Lithuania'},
            {'name': 'Michael Krmenčík', 'pos': 'ST', 'age': 28, 'rating': 81, 'nat': 'Czech Republic'},
        ]
    },

    'dynamo_kyiv': {
        'name': 'Dynamo Kyiv',
        'country': 'Ukraine',
        'league': 'Europa League',
        'players': [
            {'name': 'Heorhiy Bushchan', 'pos': 'GK', 'age': 27, 'rating': 82, 'nat': 'Ukraine'},
            {'name': 'Tomasz Kędziora', 'pos': 'RB', 'age': 27, 'rating': 83, 'nat': 'Poland'},
            {'name': 'Mykola Shaparenko', 'pos': 'CM', 'age': 24, 'rating': 84, 'nat': 'Ukraine'},
            {'name': 'Vitaliy Mykolenko', 'pos': 'LB', 'age': 24, 'rating': 82, 'nat': 'Ukraine'},
            {'name': 'Artem Besedin', 'pos': 'ST', 'age': 27, 'rating': 82, 'nat': 'Ukraine'},
            {'name': 'Viktor Tsygankov', 'pos': 'LW', 'age': 25, 'rating': 85, 'nat': 'Ukraine'},
            {'name': 'Benjamin Verbic', 'pos': 'RW', 'age': 27, 'rating': 82, 'nat': 'Slovenia'},
            {'name': 'Vitaliy Buyalskyi', 'pos': 'CM', 'age': 28, 'rating': 83, 'nat': 'Ukraine'},
            {'name': 'Ivan Petryak', 'pos': 'CAM', 'age': 27, 'rating': 81, 'nat': 'Ukraine'},
            {'name': 'Denys Popov', 'pos': 'CB', 'age': 22, 'rating': 81, 'nat': 'Ukraine'},
            {'name': 'Benjamin Sesko', 'pos': 'ST', 'age': 20, 'rating': 83, 'nat': 'Slovenia'},
        ]
    },

    'copenhagen': {
        'name': 'Copenhagen',
        'country': 'Denmark',
        'league': 'Europa League',
        'players': [
            {'name': 'Kamil Grabara', 'pos': 'GK', 'age': 25, 'rating': 83, 'nat': 'Poland'},
            {'name': 'Victor Nelsson', 'pos': 'CB', 'age': 25, 'rating': 83, 'nat': 'Denmark'},
            {'name': 'Rasmus Falk', 'pos': 'CM', 'age': 28, 'rating': 82, 'nat': 'Denmark'},
            {'name': 'Jens Stage', 'pos': 'CM', 'age': 25, 'rating': 82, 'nat': 'Denmark'},
            {'name': 'Pep Biel', 'pos': 'RW', 'age': 27, 'rating': 82, 'nat': 'Spain'},
            {'name': 'David Jensen', 'pos': 'GK', 'age': 27, 'rating': 81, 'nat': 'Denmark'},
            {'name': 'Mohammed Daramy', 'pos': 'LW', 'age': 20, 'rating': 81, 'nat': 'Denmark'},
            {'name': 'Kamil Wilczek', 'pos': 'ST', 'age': 34, 'rating': 81, 'nat': 'Poland'},
            {'name': 'Rasmus Thelander', 'pos': 'CB', 'age': 32, 'rating': 80, 'nat': 'Denmark'},
            {'name': 'Vavro', 'pos': 'CB', 'age': 28, 'rating': 81, 'nat': 'Slovakia'},
            {'name': 'Daniel Granli', 'pos': 'RB', 'age': 26, 'rating': 80, 'nat': 'Norway'},
        ]
    },

    'bodo_glimt': {
        'name': 'Bodø/Glimt',
        'country': 'Norway',
        'league': 'Europa League',
        'players': [
            {'name': 'Niklas Castro', 'pos': 'ST', 'age': 25, 'rating': 82, 'nat': 'Norway'},
            {'name': 'Joshua Smits', 'pos': 'GK', 'age': 31, 'rating': 80, 'nat': 'Netherlands'},
            {'name': 'Marius Lode', 'pos': 'LB', 'age': 28, 'rating': 81, 'nat': 'Norway'},
            {'name': 'Leo Skiri Østigård', 'pos': 'CB', 'age': 24, 'rating': 83, 'nat': 'Norway'},
            {'name': 'Patrick Berg', 'pos': 'CM', 'age': 27, 'rating': 83, 'nat': 'Norway'},
            {'name': 'Fredrik Bjørkan', 'pos': 'RB', 'age': 24, 'rating': 82, 'nat': 'Norway'},
            {'name': 'Håkon Evjen', 'pos': 'CAM', 'age': 22, 'rating': 82, 'nat': 'Norway'},
            {'name': 'Johan Hove', 'pos': 'CM', 'age': 23, 'rating': 81, 'nat': 'Norway'},
            {'name': 'Amahl Pellegrino', 'pos': 'ST', 'age': 30, 'rating': 81, 'nat': 'Norway'},
            {'name': 'Fitim Azemi', 'pos': 'RW', 'age': 28, 'rating': 80, 'nat': 'Norway'},
            {'name': 'Elias Hagen', 'pos': 'LB', 'age': 24, 'rating': 80, 'nat': 'Norway'},
        ]
    },

    'maccabi_haifa': {
        'name': 'Maccabi Haifa',
        'country': 'Israel',
        'league': 'Europa League',
        'players': [
            {'name': 'Ofir Marciano', 'pos': 'GK', 'age': 34, 'rating': 82, 'nat': 'Israel'},
            {'name': 'Yossi Benayoun', 'pos': 'CM', 'age': 40, 'rating': 80, 'nat': 'Israel'},
            {'name': 'Eli Dasa', 'pos': 'RB', 'age': 29, 'rating': 82, 'nat': 'Israel'},
            {'name': 'Rasmus Sjöstedt', 'pos': 'CB', 'age': 30, 'rating': 81, 'nat': 'Sweden'},
            {'name': 'Hatem Abd Elhamed', 'pos': 'CB', 'age': 30, 'rating': 81, 'nat': 'Israel'},
            {'name': 'Dolev Haziza', 'pos': 'RW', 'age': 28, 'rating': 82, 'nat': 'Israel'},
            {'name': 'Omer Atzili', 'pos': 'LW', 'age': 31, 'rating': 82, 'nat': 'Israel'},
            {'name': 'Yonatan Cohen', 'pos': 'CAM', 'age': 28, 'rating': 81, 'nat': 'Israel'},
            {'name': 'Nir Bitton', 'pos': 'CDM', 'age': 31, 'rating': 81, 'nat': 'Israel'},
            {'name': 'Franco', 'pos': 'ST', 'age': 28, 'rating': 82, 'nat': 'Brazil'},
            {'name': 'Gael Etock', 'pos': 'CM', 'age': 26, 'rating': 80, 'nat': 'Cameroon'},
        ]
    },

    'apoel': {
        'name': 'APOEL',
        'country': 'Cyprus',
        'league': 'Europa League',
        'players': [
            {'name': 'Uros Racic', 'pos': 'CDM', 'age': 25, 'rating': 81, 'nat': 'Serbia'},
            {'name': 'Matija Širok', 'pos': 'GK', 'age': 27, 'rating': 80, 'nat': 'Slovenia'},
            {'name': 'Cristian Ceballos', 'pos': 'RW', 'age': 27, 'rating': 80, 'nat': 'Spain'},
            {'name': 'Ivan Trickovski', 'pos': 'ST', 'age': 36, 'rating': 79, 'nat': 'Macedonia'},
            {'name': 'Mario Budimir', 'pos': 'ST', 'age': 34, 'rating': 80, 'nat': 'Croatia'},
            {'name': 'Gustavo', 'pos': 'CB', 'age': 28, 'rating': 81, 'nat': 'Brazil'},
            {'name': 'Joãozinho', 'pos': 'LB', 'age': 32, 'rating': 80, 'nat': 'Brazil'},
            {'name': 'Pieros Sotiriou', 'pos': 'ST', 'age': 30, 'rating': 82, 'nat': 'Cyprus'},
            {'name': 'Andreas Makris', 'pos': 'RW', 'age': 29, 'rating': 81, 'nat': 'Cyprus'},
            {'name': 'João Lima', 'pos': 'CM', 'age': 28, 'rating': 80, 'nat': 'Portugal'},
            {'name': 'Carlos Miguel', 'pos': 'CM', 'age': 27, 'rating': 80, 'nat': 'Portugal'},
        ]
    },

})
