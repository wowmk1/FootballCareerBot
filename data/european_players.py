# data/european_players.py
# 64 teams (32 Champions League + 32 Europa League) - 2024-style rosters
# Format: list of dicts per team, each dict: {'name','pos','age','rating','nat'}
# NO English clubs included.
# Generated for use by a Python Discord bot: TEAM_ROSTERS dictionary included at bottom.

# ---------------------------
# CHAMPIONS LEAGUE (32 teams)
# ---------------------------

REAL_MADRID_PLAYERS = [
    {'name':'Thibaut Courtois','pos':'GK','age':33,'rating':89,'nat':'Belgium'},
    {'name':'Andriy Lunin','pos':'GK','age':26,'rating':78,'nat':'Ukraine'},
    {'name':'Kepa Arrizabalaga','pos':'GK','age':30,'rating':80,'nat':'Spain'},
    {'name':'Dani Carvajal','pos':'RB','age':33,'rating':84,'nat':'Spain'},
    {'name':'Lucas Vázquez','pos':'RB','age':33,'rating':78,'nat':'Spain'},
    {'name':'Ferland Mendy','pos':'LB','age':29,'rating':83,'nat':'France'},
    {'name':'Fran García','pos':'LB','age':25,'rating':77,'nat':'Spain'},
    {'name':'Éder Militão','pos':'CB','age':27,'rating':85,'nat':'Brazil'},
    {'name':'David Alaba','pos':'CB','age':33,'rating':84,'nat':'Austria'},
    {'name':'Antonio Rüdiger','pos':'CB','age':31,'rating':87,'nat':'Germany'},
    {'name':'Nacho Fernández','pos':'CB','age':34,'rating':82,'nat':'Spain'},
    {'name':'Aurélien Tchouaméni','pos':'CDM','age':25,'rating':84,'nat':'France'},
    {'name':'Eduardo Camavinga','pos':'CM','age':22,'rating':84,'nat':'France'},
    {'name':'Luka Modrić','pos':'CM','age':39,'rating':83,'nat':'Croatia'},
    {'name':'Toni Kroos','pos':'CM','age':34,'rating':87,'nat':'Germany'},
    {'name':'Federico Valverde','pos':'CM','age':26,'rating':88,'nat':'Uruguay'},
    {'name':'Jude Bellingham','pos':'CAM','age':21,'rating':90,'nat':'England'},
    {'name':'Brahim Díaz','pos':'CAM','age':25,'rating':80,'nat':'Spain'},
    {'name':'Kylian Mbappé','pos':'ST','age':25,'rating':92,'nat':'France'},
    {'name':'Vinícius Júnior','pos':'LW','age':24,'rating':91,'nat':'Brazil'},
    {'name':'Rodrygo','pos':'RW','age':23,'rating':85,'nat':'Brazil'},
    {'name':'Joselu','pos':'ST','age':34,'rating':78,'nat':'Spain'},
    {'name':'Endrick','pos':'ST','age':18,'rating':72,'nat':'Brazil'},
    {'name':'Nico Paz','pos':'CAM','age':20,'rating':70,'nat':'Argentina'}
]

BARCELONA_PLAYERS = [
    {'name':'Marc-André ter Stegen','pos':'GK','age':33,'rating':88,'nat':'Germany'},
    {'name':'Iñaki Peña','pos':'GK','age':25,'rating':73,'nat':'Spain'},
    {'name':'Álex Remiro','pos':'GK','age':30,'rating':75,'nat':'Spain'},
    {'name':'Ronald Araújo','pos':'CB','age':25,'rating':86,'nat':'Uruguay'},
    {'name':'Jules Koundé','pos':'CB','age':25,'rating':84,'nat':'France'},
    {'name':'Pau Cubarsí','pos':'CB','age':18,'rating':72,'nat':'Spain'},
    {'name':'Jordi Alba','pos':'LB','age':35,'rating':80,'nat':'Spain'},
    {'name':'Alejandro Balde','pos':'LB','age':20,'rating':82,'nat':'Spain'},
    {'name':'Dani Alves','pos':'RB','age':40,'rating':68,'nat':'Brazil'},
    {'name':'Sergio Busquets','pos':'CDM','age':35,'rating':79,'nat':'Spain'},
    {'name':'Frenkie de Jong','pos':'CM','age':27,'rating':86,'nat':'Netherlands'},
    {'name':'Pedri','pos':'CM','age':21,'rating':86,'nat':'Spain'},
    {'name':'Gavi','pos':'CM','age':19,'rating':84,'nat':'Spain'},
    {'name':'Franck Kessié','pos':'CM','age':27,'rating':81,'nat':'Ivory Coast'},
    {'name':'Robert Lewandowski','pos':'ST','age':36,'rating':86,'nat':'Poland'},
    {'name':'Raphinha','pos':'RW','age':27,'rating':83,'nat':'Brazil'},
    {'name':'Ousmane Dembélé','pos':'RW','age':26,'rating':83,'nat':'France'},
    {'name':'Ansu Fati','pos':'LW','age':21,'rating':78,'nat':'Spain'},
    {'name':'Ferran Torres','pos':'ST','age':24,'rating':80,'nat':'Spain'},
    {'name':'Pablo Torre','pos':'CAM','age':20,'rating':74,'nat':'Spain'},
    {'name':'Lamine Yamal','pos':'RW','age':16,'rating':83,'nat':'Spain'},
    {'name':'Fermín López','pos':'CM','age':22,'rating':76,'nat':'Spain'},
    {'name':'Inigo Martinez','pos':'CB','age':33,'rating':80,'nat':'Spain'}
]

ATLETICO_MADRID_PLAYERS = [
    {'name':'Jan Oblak','pos':'GK','age':31,'rating':88,'nat':'Slovenia'},
    {'name':'Aitor Fernández','pos':'GK','age':32,'rating':74,'nat':'Spain'},
    {'name':'Stefan Savić','pos':'CB','age':34,'rating':80,'nat':'Montenegro'},
    {'name':'José María Giménez','pos':'CB','age':29,'rating':83,'nat':'Uruguay'},
    {'name':'Mario Hermoso','pos':'CB','age':29,'rating':81,'nat':'Spain'},
    {'name':'Felipe','pos':'CB','age':36,'rating':76,'nat':'Brazil'},
    {'name':'Kieran Trippier','pos':'RB','age':33,'rating':82,'nat':'England'},
    {'name':'Nahuel Molina','pos':'RB','age':26,'rating':78,'nat':'Argentina'},
    {'name':'Sergio Reguilón','pos':'LB','age':28,'rating':78,'nat':'Spain'},
    {'name':'Koke','pos':'CM','age':32,'rating':81,'nat':'Spain'},
    {'name':'Rodrigo De Paul','pos':'CM','age':29,'rating':82,'nat':'Argentina'},
    {'name':'Marcos Llorente','pos':'CM','age':29,'rating':83,'nat':'Spain'},
    {'name':'Saúl Ñíguez','pos':'CM','age':29,'rating':77,'nat':'Spain'},
    {'name':'Antoine Griezmann','pos':'FW','age':33,'rating':84,'nat':'France'},
    {'name':'Álvaro Morata','pos':'ST','age':31,'rating':80,'nat':'Spain'},
    {'name':'João Félix','pos':'FW','age':25,'rating':81,'nat':'Portugal'},
    {'name':'Thomas Lemar','pos':'LW','age':28,'rating':79,'nat':'France'},
    {'name':'Ángel Correa','pos':'RW','age':29,'rating':80,'nat':'Argentina'},
    {'name':'Matheus Cunha','pos':'ST','age':25,'rating':78,'nat':'Brazil'},
    {'name':'Viktor Torrejón','pos':'CB','age':22,'rating':72,'nat':'Spain'},
    {'name':'Pablo Barrios','pos':'CM','age':20,'rating':73,'nat':'Spain'},
    {'name':'Iván Saponjic','pos':'ST','age':24,'rating':70,'nat':'Serbia'},
    {'name':'Luca Romero','pos':'CM','age':18,'rating':69,'nat':'Argentina'}
]

SEVILLA_PLAYERS = [
    {'name':'Yassine Bounou','pos':'GK','age':33,'rating':80,'nat':'Morocco'},
    {'name':'Marko Dmitrović','pos':'GK','age':32,'rating':74,'nat':'Serbia'},
    {'name':'Alejandro Acevedo','pos':'GK','age':21,'rating':66,'nat':'Spain'},
    {'name':'Sergio Ramos','pos':'CB','age':38,'rating':77,'nat':'Spain'},
    {'name':'Diego Carlos','pos':'CB','age':31,'rating':79,'nat':'Brazil'},
    {'name':'Marcao','pos':'CB','age':28,'rating':77,'nat':'Brazil'},
    {'name':'Kike Salas','pos':'CB','age':23,'rating':71,'nat':'Spain'},
    {'name':'Gonzalo Montiel','pos':'RB','age':28,'rating':78,'nat':'Argentina'},
    {'name':'Jesús Navas','pos':'RB','age':38,'rating':75,'nat':'Spain'},
    {'name':'Nemanja Gudelj','pos':'CDM','age':32,'rating':77,'nat':'Serbia'},
    {'name':'Joan Jordán','pos':'CM','age':30,'rating':80,'nat':'Spain'},
    {'name':'Óliver Torres','pos':'CM','age':31,'rating':75,'nat':'Spain'},
    {'name':'Fernando','pos':'CDM','age':36,'rating':72,'nat':'Brazil'},
    {'name':'Isco','pos':'CAM','age':32,'rating':74,'nat':'Spain'},
    {'name':'Bryan Gil','pos':'RW','age':23,'rating':76,'nat':'Spain'},
    {'name':'Youssef En-Nesyri','pos':'ST','age':27,'rating':79,'nat':'Morocco'},
    {'name':'Rafa Mir','pos':'ST','age':27,'rating':75,'nat':'Spain'},
    {'name':'Suso','pos':'AM','age':30,'rating':76,'nat':'Spain'},
    {'name':'Julen Lobete','pos':'W','age':22,'rating':72,'nat':'Spain'},
    {'name':'Eran Zahavi','pos':'ST','age':36,'rating':73,'nat':'Israel'},
    {'name':'Sergio Escudero','pos':'LB','age':33,'rating':72,'nat':'Spain'},
    {'name':'Iván Romero','pos':'ST','age':24,'rating':70,'nat':'Spain'},
    {'name':'Juanpe','pos':'CB','age':31,'rating':70,'nat':'Spain'}
]

# 5-8: Germany (Bayern, Dortmund, RB Leipzig, Bayer Leverkusen)

BAYERN_MUNICH_PLAYERS = [
    {'name':'Manuel Neuer','pos':'GK','age':39,'rating':86,'nat':'Germany'},
    {'name':'Sven Ulreich','pos':'GK','age':36,'rating':74,'nat':'Germany'},
    {'name':'Kingsley Coman','pos':'LW','age':29,'rating':84,'nat':'France'},
    {'name':'Leroy Sané','pos':'RW','age':29,'rating':85,'nat':'Germany'},
    {'name':'Serge Gnabry','pos':'RW','age':30,'rating':83,'nat':'Germany'},
    {'name':'Harry Kane','pos':'ST','age':32,'rating':91,'nat':'England'},
    {'name':'Jamal Musiala','pos':'CAM','age':22,'rating':88,'nat':'Germany'},
    {'name':'Joshua Kimmich','pos':'CDM','age':30,'rating':87,'nat':'Germany'},
    {'name':'Leon Goretzka','pos':'CM','age':30,'rating':84,'nat':'Germany'},
    {'name':'Dayot Upamecano','pos':'CB','age':26,'rating':84,'nat':'France'},
    {'name':'Matthijs de Ligt','pos':'CB','age':26,'rating':85,'nat':'Netherlands'},
    {'name':'Alphonso Davies','pos':'LB','age':24,'rating':84,'nat':'Canada'},
    {'name':'Noussair Mazraoui','pos':'RB','age':27,'rating':80,'nat':'Morocco'},
    {'name':'Min-jae Kim','pos':'CB','age':28,'rating':83,'nat':'South Korea'},
    {'name':'Thomas Müller','pos':'CF','age':36,'rating':80,'nat':'Germany'},
    {'name':'Konrad Laimer','pos':'CM','age':27,'rating':79,'nat':'Austria'},
    {'name':'Mathys Tel','pos':'ST','age':19,'rating':76,'nat':'France'},
    {'name':'Eric Maxim Choupo-Moting','pos':'ST','age':35,'rating':75,'nat':'Cameroon'},
    {'name':'Raphaël Guerreiro','pos':'LB','age':31,'rating':80,'nat':'Portugal'},
    {'name':'Dayot Upamecano','pos':'CB','age':26,'rating':84,'nat':'France'},
    {'name':'Aleksandar Pavlović','pos':'CM','age':21,'rating':76,'nat':'Germany'},
    {'name':'Lukas Mai','pos':'CB','age':23,'rating':70,'nat':'Germany'},
    {'name':'Marcel Sabitzer','pos':'CM','age':31,'rating':81,'nat':'Austria'}
]

BORUSSIA_DORTMUND_PLAYERS = [
    {'name':'Gregor Kobel','pos':'GK','age':27,'rating':84,'nat':'Switzerland'},
    {'name':'Alexander Meyer','pos':'GK','age':34,'rating':73,'nat':'Germany'},
    {'name':'Mats Hummels','pos':'CB','age':36,'rating':81,'nat':'Germany'},
    {'name':'Nico Schlotterbeck','pos':'CB','age':25,'rating':83,'nat':'Germany'},
    {'name':'Niklas Süle','pos':'CB','age':30,'rating':82,'nat':'Germany'},
    {'name':'Donyell Malen','pos':'ST','age':26,'rating':82,'nat':'Netherlands'},
    {'name':'Youssoufa Moukoko','pos':'ST','age':20,'rating':77,'nat':'Germany'},
    {'name':'Karim Adeyemi','pos':'RW','age':23,'rating':81,'nat':'Germany'},
    {'name':'Jadon Sancho','pos':'LW','age':25,'rating':84,'nat':'England'},
    {'name':'Julian Brandt','pos':'CAM','age':29,'rating':83,'nat':'Germany'},
    {'name':'Emre Can','pos':'CDM','age':31,'rating':82,'nat':'Germany'},
    {'name':'Marcel Sabitzer','pos':'CM','age':31,'rating':81,'nat':'Austria'},
    {'name':'Felix Nmecha','pos':'CM','age':24,'rating':77,'nat':'Germany'},
    {'name':'Ian Maatsen','pos':'LB','age':23,'rating':79,'nat':'Netherlands'},
    {'name':'Julian Ryerson','pos':'RB','age':27,'rating':78,'nat':'Norway'},
    {'name':'Sebastien Haller','pos':'ST','age':30,'rating':80,'nat':'Ivory Coast'},
    {'name':'Thomas Meunier','pos':'RB','age':32,'rating':76,'nat':'Belgium'},
    {'name':'Donyell Malen','pos':'ST','age':26,'rating':82,'nat':'Netherlands'},
    {'name':'Alexander Isak','pos':'ST','age':26,'rating':84,'nat':'Sweden'},
    {'name':'Mateu Morey','pos':'RB','age':23,'rating':72,'nat':'Spain'},
    {'name':'Niclas Füllkrug','pos':'ST','age':31,'rating':78,'nat':'Germany'},
    {'name':'Julian Weigl','pos':'CM','age':28,'rating':74,'nat':'Germany'},
    {'name':'Emre Özkan','pos':'CB','age':22,'rating':70,'nat':'Turkey'}
]

RB_LEIPZIG_PLAYERS = [
    {'name':'Janis Blaswich','pos':'GK','age':33,'rating':76,'nat':'Germany'},
    {'name':'Peter Gulacsi','pos':'GK','age':33,'rating':77,'nat':'Hungary'},
    {'name':'Dominik Szoboszlai','pos':'CM','age':24,'rating':86,'nat':'Hungary'},
    {'name':'Benjamin Henrichs','pos':'RB','age':27,'rating':77,'nat':'Germany'},
    {'name':'Ibrahima Konaté','pos':'CB','age':24,'rating':82,'nat':'France'},
    {'name':'Mohamed Simakan','pos':'CB','age':22,'rating':76,'nat':'France'},
    {'name':'Willi Orban','pos':'CB','age':31,'rating':77,'nat':'Hungary'},
    {'name':'Konrad Laimer','pos':'CM','age':27,'rating':79,'nat':'Austria'},
    {'name':'Xavi Simons','pos':'CAM','age':20,'rating':78,'nat':'Netherlands'},
    {'name':'Yussuf Poulsen','pos':'ST','age':29,'rating':77,'nat':'Denmark'},
    {'name':'Patrik Schick','pos':'ST','age':27,'rating':81,'nat':'Czech Republic'},
    {'name':'Amadou Haidara','pos':'CM','age':25,'rating':80,'nat':'Mali'},
    {'name':'Christopher Nkunku','pos':'FW','age':25,'rating':85,'nat':'France'},
    {'name':'Nkunku','pos':'FW','age':25,'rating':85,'nat':'France'},
    {'name':'Jan-Niklas Beste','pos':'LW','age':23,'rating':71,'nat':'Germany'},
    {'name':'Fabio Carvalho','pos':'RW','age':21,'rating':75,'nat':'Portugal'},
    {'name':'Joško Gvardiol','pos':'CB','age':20,'rating':83,'nat':'Croatia'},
    {'name':'Kevin Kampl','pos':'CM','age':32,'rating':75,'nat':'Slovenia'},
    {'name':'Benjamin Šeško','pos':'ST','age':19,'rating':77,'nat':'Slovenia'},
    {'name':'Maximilian Wöber','pos':'CB','age':26,'rating':76,'nat':'Austria'},
    {'name':'Moussa Diaby','pos':'RW','age':24,'rating':82,'nat':'France'},
    {'name':'Yussuf Poulsen','pos':'ST','age':29,'rating':77,'nat':'Denmark'}
]

BAYER_LEVERKUSEN_PLAYERS = [
    {'name':'Lukas Hradecky','pos':'GK','age':34,'rating':83,'nat':'Finland'},
    {'name':'Finn Dahmen','pos':'GK','age':25,'rating':72,'nat':'Germany'},
    {'name':'Jeremie Frimpong','pos':'RB','age':23,'rating':81,'nat':'Netherlands'},
    {'name':'Piero Hincapié','pos':'CB','age':21,'rating':80,'nat':'Ecuador'},
    {'name':'Jonathan Tah','pos':'CB','age':27,'rating':80,'nat':'Germany'},
    {'name':'Nico Schlotterbeck','pos':'CB','age':25,'rating':83,'nat':'Germany'},
    {'name':'Edmond Tapsoba','pos':'CB','age':25,'rating':81,'nat':'Burkina Faso'},
    {'name':'Exequiel Palacios','pos':'CM','age':25,'rating':80,'nat':'Argentina'},
    {'name':'Florian Wirtz','pos':'CAM','age':20,'rating':86,'nat':'Germany'},
    {'name':'Moussa Diaby','pos':'RW','age':24,'rating':82,'nat':'France'},
    {'name':'Robert Andrich','pos':'CDM','age':29,'rating':77,'nat':'Germany'},
    {'name':'Victor Boniface','pos':'ST','age':21,'rating':80,'nat':'Nigeria'},
    {'name':'Amine Adli','pos':'LW','age':23,'rating':77,'nat':'France'},
    {'name':'Sandro Tonali','pos':'CM','age':23,'rating':84,'nat':'Italy'},
    {'name':'Moussa Diaby','pos':'RW','age':24,'rating':82,'nat':'France'},
    {'name':'Kerem Demirbay','pos':'CM','age':29,'rating':78,'nat':'Germany'},
    {'name':'Nadiem Amiri','pos':'CAM','age':27,'rating':76,'nat':'Germany'},
    {'name':'Wendell','pos':'LB','age':32,'rating':78,'nat':'Brazil'},
    {'name':'Hincapié','pos':'CB','age':21,'rating':80,'nat':'Ecuador'},
    {'name':'Jeremie Frimpong','pos':'RB','age':23,'rating':81,'nat':'Netherlands'},
    {'name':'Mitchel Bakker','pos':'LB','age':23,'rating':76,'nat':'Netherlands'},
    {'name':'Aleksandar Dragović','pos':'CB','age':33,'rating':72,'nat':'Austria'}
]

# ---------------------------
# Champions League - Italy (9-12)
# ---------------------------

INTER_MILAN_PLAYERS = [
    {'name':'Yann Sommer','pos':'GK','age':36,'rating':84,'nat':'Switzerland'},
    {'name':'André Onana','pos':'GK','age':28,'rating':85,'nat':'Cameroon'},
    {'name':'Francesco Acerbi','pos':'CB','age':37,'rating':81,'nat':'Italy'},
    {'name':'Stefan de Vrij','pos':'CB','age':33,'rating':82,'nat':'Netherlands'},
    {'name':'Alessandro Bastoni','pos':'CB','age':26,'rating':85,'nat':'Italy'},
    {'name':'Milan Škriniar','pos':'CB','age':29,'rating':84,'nat':'Slovakia'},
    {'name':'Denzel Dumfries','pos':'RB','age':29,'rating':82,'nat':'Netherlands'},
    {'name':'Federico Dimarco','pos':'LB','age':27,'rating':84,'nat':'Italy'},
    {'name':'Nicolo Barella','pos':'CM','age':28,'rating':87,'nat':'Italy'},
    {'name':'Hakan Çalhanoğlu','pos':'CM','age':31,'rating':86,'nat':'Turkey'},
    {'name':'Marko Arnautović','pos':'ST','age':36,'rating':76,'nat':'Austria'},
    {'name':'Lautaro Martínez','pos':'ST','age':28,'rating':89,'nat':'Argentina'},
    {'name':'Marcus Thuram','pos':'ST','age':28,'rating':84,'nat':'France'},
    {'name':'Henrikh Mkhitaryan','pos':'CM','age':36,'rating':80,'nat':'Armenia'},
    {'name':'Davide Frattesi','pos':'CM','age':25,'rating':81,'nat':'Italy'},
    {'name':'Juan Cuadrado','pos':'RW','age':37,'rating':75,'nat':'Colombia'},
    {'name':'Marcus Thuram','pos':'ST','age':28,'rating':84,'nat':'France'},
    {'name':'Bastoni','pos':'CB','age':26,'rating':85,'nat':'Italy'},
    {'name':'Yann Aurel','pos':'GK','age':20,'rating':70,'nat':'Italy'},
    {'name':'Eddie Salcedo','pos':'ST','age':22,'rating':72,'nat':'Italy'},
    {'name':'Kristjan Asllani','pos':'CM','age':22,'rating':75,'nat':'Albania'},
    {'name':'Matías Vecino','pos':'CM','age':32,'rating':74,'nat':'Uruguay'}
]

AC_MILAN_PLAYERS = [
    {'name':'Mike Maignan','pos':'GK','age':30,'rating':87,'nat':'France'},
    {'name':'Marco Sportiello','pos':'GK','age':33,'rating':76,'nat':'Italy'},
    {'name':'Theo Hernández','pos':'LB','age':28,'rating':86,'nat':'France'},
    {'name':'Fikayo Tomori','pos':'CB','age':27,'rating':83,'nat':'England'},
    {'name':'Malick Thiaw','pos':'CB','age':24,'rating':80,'nat':'Germany'},
    {'name':'Pierre Kalulu','pos':'RB','age':25,'rating':79,'nat':'France'},
    {'name':'Alessandro Florenzi','pos':'RB','age':34,'rating':76,'nat':'Italy'},
    {'name':'Ismaël Bennacer','pos':'CDM','age':27,'rating':83,'nat':'Algeria'},
    {'name':'Yunus Musah','pos':'CM','age':22,'rating':78,'nat':'USA'},
    {'name':'Ruben Loftus-Cheek','pos':'CM','age':29,'rating':81,'nat':'England'},
    {'name':'Christian Pulisic','pos':'RW','age':26,'rating':83,'nat':'USA'},
    {'name':'Rafael Leão','pos':'LW','age':26,'rating':87,'nat':'Portugal'},
    {'name':'Olivier Giroud','pos':'ST','age':39,'rating':80,'nat':'France'},
    {'name':'Noah Okafor','pos':'ST','age':25,'rating':79,'nat':'Switzerland'},
    {'name':'Junior Messias','pos':'RW','age':31,'rating':72,'nat':'Brazil'},
    {'name':'Samuel Chukwueze','pos':'RW','age':26,'rating':80,'nat':'Nigeria'},
    {'name':'Brahim Díaz','pos':'CAM','age':25,'rating':80,'nat':'Spain'},
    {'name':'Soualiho Meïté','pos':'CDM','age':30,'rating':72,'nat':'France'},
    {'name':'Davide Calabria','pos':'RB','age':27,'rating':77,'nat':'Italy'},
    {'name':'Tiemoué Bakayoko','pos':'CM','age':29,'rating':73,'nat':'France'},
    {'name':'Zlatan Ibrahimović','pos':'ST','age':43,'rating':65,'nat':'Sweden'},
    {'name':'Maignan','pos':'GK','age':30,'rating':87,'nat':'France'}
]

JUVENTUS_PLAYERS = [
    {'name':'Wojciech Szczęsny','pos':'GK','age':35,'rating':84,'nat':'Poland'},
    {'name':'Mattia Perin','pos':'GK','age':32,'rating':78,'nat':'Italy'},
    {'name':'Gleison Bremer','pos':'CB','age':28,'rating':85,'nat':'Brazil'},
    {'name':'Danilo','pos':'CB','age':34,'rating':82,'nat':'Brazil'},
    {'name':'Federico Gatti','pos':'CB','age':27,'rating':79,'nat':'Italy'},
    {'name':'Alex Sandro','pos':'LB','age':34,'rating':76,'nat':'Brazil'},
    {'name':'Andrea Cambiaso','pos':'LB','age':25,'rating':78,'nat':'Italy'},
    {'name':'Manuel Locatelli','pos':'CDM','age':27,'rating':82,'nat':'Italy'},
    {'name':'Adrien Rabiot','pos':'CM','age':30,'rating':83,'nat':'France'},
    {'name':'Weston McKennie','pos':'CM','age':27,'rating':80,'nat':'USA'},
    {'name':'Nicolò Fagioli','pos':'CM','age':25,'rating':78,'nat':'Italy'},
    {'name':'Federico Chiesa','pos':'LW','age':28,'rating':84,'nat':'Italy'},
    {'name':'Timothy Weah','pos':'RW','age':25,'rating':77,'nat':'USA'},
    {'name':'Dušan Vlahović','pos':'ST','age':25,'rating':85,'nat':'Serbia'},
    {'name':'Arkadiusz Milik','pos':'ST','age':31,'rating':78,'nat':'Poland'},
    {'name':'Moise Kean','pos':'ST','age':24,'rating':77,'nat':'Italy'},
    {'name':'Kaio Jorge','pos':'ST','age':22,'rating':72,'nat':'Brazil'},
    {'name':'Stefan de Vrij','pos':'CB','age':33,'rating':82,'nat':'Netherlands'},
    {'name':'Gleison Bremer','pos':'CB','age':28,'rating':85,'nat':'Brazil'},
    {'name':'Federico Gatti','pos':'CB','age':27,'rating':79,'nat':'Italy'},
    {'name':'Matias Soulé','pos':'RW','age':20,'rating':72,'nat':'Argentina'},
    {'name':'Nicolo Fagioli','pos':'CM','age':25,'rating':78,'nat':'Italy'}
]

NAPOLI_PLAYERS = [
    {'name':'Alex Meret','pos':'GK','age':28,'rating':81,'nat':'Italy'},
    {'name':'David Ospina','pos':'GK','age':34,'rating':78,'nat':'Colombia'},
    {'name':'Giovanni Di Lorenzo','pos':'RB','age':31,'rating':84,'nat':'Italy'},
    {'name':'Amir Rrahmani','pos':'CB','age':31,'rating':82,'nat':'Kosovo'},
    {'name':'Juan Jesus','pos':'CB','age':34,'rating':75,'nat':'Brazil'},
    {'name':'Leo Østigård','pos':'CB','age':25,'rating':77,'nat':'Norway'},
    {'name':'Mathías Olivera','pos':'LB','age':27,'rating':79,'nat':'Uruguay'},
    {'name':'Stanislav Lobotka','pos':'CDM','age':30,'rating':83,'nat':'Slovakia'},
    {'name':'Piotr Zieliński','pos':'CM','age':31,'rating':82,'nat':'Poland'},
    {'name':'André-Frank Zambo Anguissa','pos':'CM','age':29,'rating':83,'nat':'Cameroon'},
    {'name':'Khvicha Kvaratskhelia','pos':'LW','age':24,'rating':86,'nat':'Georgia'},
    {'name':'Matteo Politano','pos':'RW','age':32,'rating':81,'nat':'Italy'},
    {'name':'Victor Osimhen','pos':'ST','age':26,'rating':88,'nat':'Nigeria'},
    {'name':'Giacomo Raspadori','pos':'CF','age':25,'rating':80,'nat':'Italy'},
    {'name':'Giovanni Simeone','pos':'ST','age':30,'rating':79,'nat':'Argentina'},
    {'name':'Hirving Lozano','pos':'RW','age':28,'rating':78,'nat':'Mexico'},
    {'name':'Koulibaly','pos':'CB','age':33,'rating':80,'nat':'Senegal'},
    {'name':'Nicolas Dominguez','pos':'CM','age':26,'rating':75,'nat':'Argentina'},
    {'name':'Amir Rrahmani','pos':'CB','age':31,'rating':82,'nat':'Kosovo'},
    {'name':'Andrea Petagna','pos':'ST','age':31,'rating':74,'nat':'Italy'},
    {'name':'Eljif Elmas','pos':'CM','age':23,'rating':76,'nat':'North Macedonia'},
    {'name':'Ionut Radu','pos':'GK','age':25,'rating':70,'nat':'Romania'}
]

# ---------------------------
# France (13-16)
# ---------------------------

PARIS_SAINT_GERMAIN_PLAYERS = [
    {'name':'Gianluigi Donnarumma','pos':'GK','age':26,'rating':86,'nat':'Italy'},
    {'name':'Alphonse Areola','pos':'GK','age':31,'rating':75,'nat':'France'},
    {'name':'Achraf Hakimi','pos':'RB','age':26,'rating':86,'nat':'Morocco'},
    {'name':'Marquinhos','pos':'CB','age':30,'rating':86,'nat':'Brazil'},
    {'name':'Lucas Hernández','pos':'CB','age':29,'rating':84,'nat':'France'},
    {'name':'Presnel Kimpembe','pos':'CB','age':28,'rating':81,'nat':'France'},
    {'name':'Nuno Mendes','pos':'LB','age':23,'rating':83,'nat':'Portugal'},
    {'name':'Danilo Pereira','pos':'CDM','age':33,'rating':79,'nat':'Portugal'},
    {'name':'Marco Verratti','pos':'CM','age':31,'rating':84,'nat':'Italy'},
    {'name':'Vitinha','pos':'CM','age':25,'rating':83,'nat':'Portugal'},
    {'name':'Warren Zaïre-Emery','pos':'CM','age':19,'rating':80,'nat':'France'},
    {'name':'Ousmane Dembélé','pos':'RW','age':28,'rating':84,'nat':'France'},
    {'name':'Kylian Mbappé','pos':'ST','age':26,'rating':92,'nat':'France'},
    {'name':'Neymar','pos':'LW','age':32,'rating':89,'nat':'Brazil'},
    {'name':'Randal Kolo Muani','pos':'ST','age':26,'rating':83,'nat':'France'},
    {'name':'Gonçalo Ramos','pos':'ST','age':24,'rating':82,'nat':'Portugal'},
    {'name':'Gianluca Scamacca','pos':'ST','age':25,'rating':78,'nat':'Italy'},
    {'name':'Fabian Ruiz','pos':'CM','age':28,'rating':82,'nat':'Spain'},
    {'name':'Vitinha','pos':'CM','age':25,'rating':83,'nat':'Portugal'},
    {'name':'Luis Enrique','pos':'Coach','age':53,'rating':0,'nat':'Spain'}  # coach placeholder
]

MARSEILLE_PLAYERS = [
    {'name':'Pau López','pos':'GK','age':30,'rating':80,'nat':'Spain'},
    {'name':'Lionel Gomez','pos':'GK','age':22,'rating':68,'nat':'France'},
    {'name':'Jonathan Clauss','pos':'RB','age':32,'rating':82,'nat':'France'},
    {'name':'Samuel Gigot','pos':'CB','age':31,'rating':79,'nat':'France'},
    {'name':'Leonardo Balerdi','pos':'CB','age':26,'rating':78,'nat':'Argentina'},
    {'name':'Chancel Mbemba','pos':'CB','age':30,'rating':80,'nat':'DR Congo'},
    {'name':'Renan Lodi','pos':'LB','age':27,'rating':79,'nat':'Brazil'},
    {'name':'Geoffrey Kondogbia','pos':'CDM','age':32,'rating':80,'nat':'Central African Republic'},
    {'name':'Jordan Veretout','pos':'CM','age':32,'rating':81,'nat':'France'},
    {'name':'Azzedine Ounahi','pos':'CM','age':24,'rating':78,'nat':'Morocco'},
    {'name':'Ismaïla Sarr','pos':'RW','age':27,'rating':81,'nat':'Senegal'},
    {'name':'Pierre-Emerick Aubameyang','pos':'ST','age':36,'rating':80,'nat':'Gabon'},
    {'name':'Iliman Ndiaye','pos':'CF','age':25,'rating':77,'nat':'Senegal'},
    {'name':'Amine Harit','pos':'CAM','age':28,'rating':79,'nat':'Morocco'},
    {'name':'Luis Henrique','pos':'LW','age':23,'rating':75,'nat':'Brazil'},
    {'name':'Pol Lirola','pos':'RB','age':26,'rating':76,'nat':'Spain'},
    {'name':'Konrad de la Fuente','pos':'LW','age':23,'rating':72,'nat':'USA'},
    {'name':'Jordan Amavi','pos':'LB','age':31,'rating':71,'nat':'France'},
    {'name':'Gerson','pos':'CM','age':27,'rating':77,'nat':'Brazil'},
    {'name':'Pape Gueye','pos':'CDM','age':25,'rating':73,'nat':'Senegal'},
    {'name':'Leonardo Jardim','pos':'Coach','age':49,'rating':0,'nat':'Portugal'}
]

MONACO_PLAYERS = [
    {'name':'Philipp Köhn','pos':'GK','age':27,'rating':79,'nat':'Switzerland'},
    {'name':'Radoslaw Majecki','pos':'GK','age':25,'rating':73,'nat':'Poland'},
    {'name':'Alexander Nübel','pos':'GK','age':27,'rating':77,'nat':'Germany'},
    {'name':'Guillermo Maripán','pos':'CB','age':31,'rating':79,'nat':'Chile'},
    {'name':'Axel Disasi','pos':'CB','age':25,'rating':80,'nat':'France'},
    {'name':'Thilo Kehrer','pos':'CB','age':28,'rating':78,'nat':'Germany'},
    {'name':'Caio Henrique','pos':'LB','age':27,'rating':80,'nat':'Brazil'},
    {'name':'Youssouf Fofana','pos':'CM','age':26,'rating':82,'nat':'France'},
    {'name':'Denis Zakaria','pos':'CDM','age':28,'rating':80,'nat':'Switzerland'},
    {'name':'Aleksandr Golovin','pos':'CAM','age':28,'rating':81,'nat':'Russia'},
    {'name':'Wissam Ben Yedder','pos':'ST','age':35,'rating':82,'nat':'France'},
    {'name':'Folarin Balogun','pos':'ST','age':24,'rating':81,'nat':'USA'},
    {'name':'Takumi Minamino','pos':'RW','age':30,'rating':79,'nat':'Japan'},
    {'name':'Krépin Diatta','pos':'RW','age':26,'rating':78,'nat':'Senegal'},
    {'name':'Aurelien Tchouameni','pos':'CM','age':24,'rating':85,'nat':'France'},  # note: placeholder if transferred
    {'name':'Maghnes Akliouche','pos':'CAM','age':22,'rating':76,'nat':'France'},
    {'name':'Eddie Salcedo','pos':'ST','age':22,'rating':72,'nat':'Italy'},
    {'name':'Elios','pos':'LB','age':20,'rating':67,'nat':'Portugal'},
    {'name':'Ludovic Blas','pos':'CAM','age':27,'rating':80,'nat':'France'},
    {'name':'Caio','pos':'RB','age':24,'rating':70,'nat':'Brazil'},
    {'name':'Sofiane Diop','pos':'RW','age':22,'rating':74,'nat':'France'},
    {'name':'Philipp','pos':'GK','age':22,'rating':65,'nat':'Germany'}
]

LYON_PLAYERS = [
    {'name':'Anthony Lopes','pos':'GK','age':34,'rating':80,'nat':'Portugal'},
    {'name':'Julian Pollersbeck','pos':'GK','age':30,'rating':72,'nat':'Germany'},
    {'name':'Nicolás Tagliafico','pos':'LB','age':32,'rating':81,'nat':'Argentina'},
    {'name':'Castello Lukeba','pos':'CB','age':20,'rating':77,'nat':'France'},
    {'name':'Jason Denayer','pos':'CB','age':28,'rating':77,'nat':'Belgium'},
    {'name':'Joelinton','pos':'CB','age':27,'rating':74,'nat':'Brazil'},
    {'name':'Clinton Mata','pos':'RB','age':32,'rating':77,'nat':'Angola'},
    {'name':'Corentin Tolisso','pos':'CM','age':30,'rating':79,'nat':'France'},
    {'name':'Maxence Caqueret','pos':'CM','age':25,'rating':81,'nat':'France'},
    {'name':'Rayan Cherki','pos':'CAM','age':21,'rating':79,'nat':'France'},
    {'name':'Ernest Nuamah','pos':'RW','age':21,'rating':78,'nat':'Ghana'},
    {'name':'Alexandre Lacazette','pos':'ST','age':34,'rating':82,'nat':'France'},
    {'name':'Saël Kumbedi','pos':'RB','age':20,'rating':75,'nat':'France'},
    {'name':'Mama Baldé','pos':'ST','age':29,'rating':77,'nat':'Guinea-Bissau'},
    {'name':'Sinaly Diomande','pos':'CB','age':22,'rating':74,'nat':'Ivory Coast'},
    {'name':'Gerson','pos':'CM','age':27,'rating':77,'nat':'Brazil'},
    {'name':'Karl Toko Ekambi','pos':'RW','age':31,'rating':76,'nat':'Cameroon'},
    {'name':'Sacha Boey','pos':'RB','age':23,'rating':73,'nat':'Cameroon'},
    {'name':'Thiago Mendes','pos':'CDM','age':31,'rating':73,'nat':'Brazil'},
    {'name':'Rayan Aït-Nouri','pos':'LB','age':23,'rating':72,'nat':'Algeria'},
    {'name':'Moussa Dembélé','pos':'ST','age':27,'rating':75,'nat':'France'},
    {'name':'Tiago Djaló','pos':'CB','age':23,'rating':72,'nat':'Portugal'}
]

# ---------------------------
# Portugal (17-19)
# ---------------------------

BENFICA_PLAYERS = [
    {'name':'Anatoliy Trubin','pos':'GK','age':24,'rating':81,'nat':'Ukraine'},
    {'name':'Odysseas Vlachodimos','pos':'GK','age':29,'rating':77,'nat':'Greece'},
    {'name':'António Silva','pos':'CB','age':21,'rating':81,'nat':'Portugal'},
    {'name':'Nicolás Otamendi','pos':'CB','age':37,'rating':78,'nat':'Argentina'},
    {'name':'Roman Yaremchuk','pos':'ST','age':27,'rating':77,'nat':'Ukraine'},
    {'name':'Petar Musa','pos':'ST','age':27,'rating':78,'nat':'Croatia'},
    {'name':'Rafa Silva','pos':'CAM','age':32,'rating':83,'nat':'Portugal'},
    {'name':'Diogo Gonçalves','pos':'RW','age':25,'rating':75,'nat':'Portugal'},
    {'name':'Orkun Kökçü','pos':'CM','age':24,'rating':81,'nat':'Turkey'},
    {'name':'João Neves','pos':'CDM','age':20,'rating':80,'nat':'Portugal'},
    {'name':'Ángel Di María','pos':'RW','age':36,'rating':83,'nat':'Argentina'},
    {'name':'David Neres','pos':'RW','age':28,'rating':80,'nat':'Brazil'},
    {'name':'Lucas Veríssimo','pos':'CB','age':30,'rating':76,'nat':'Brazil'},
    {'name':'Alex Grimaldo','pos':'LB','age':28,'rating':78,'nat':'Spain'},
    {'name':'Grimaldo','pos':'LB','age':28,'rating':78,'nat':'Spain'},
    {'name':'Lazar Randjelovic','pos':'LW','age':24,'rating':71,'nat':'Serbia'},
    {'name':'Bernardo','pos':'CM','age':23,'rating':72,'nat':'Portugal'},
    {'name':'Enzo','pos':'CM','age':20,'rating':69,'nat':'Portugal'},
    {'name':'Tay','pos':'RB','age':22,'rating':68,'nat':'Portugal'},
    {'name':'Benfica Youth','pos':'SUB','age':18,'rating':65,'nat':'Portugal'},
    {'name':'Rafa Silva','pos':'RW','age':32,'rating':83,'nat':'Portugal'}
]

PORTO_PLAYERS = [
    {'name':'Diogo Costa','pos':'GK','age':25,'rating':84,'nat':'Portugal'},
    {'name':'Iván Jaime','pos':'CM','age':24,'rating':75,'nat':'Spain'},
    {'name':'Pepe','pos':'CB','age':42,'rating':77,'nat':'Portugal'},
    {'name':'Evanilson','pos':'ST','age':26,'rating':82,'nat':'Brazil'},
    {'name':'Galeno','pos':'LW','age':27,'rating':82,'nat':'Brazil'},
    {'name':'Otávio','pos':'RW','age':30,'rating':82,'nat':'Portugal'},
    {'name':'Wendell','pos':'LB','age':32,'rating':78,'nat':'Brazil'},
    {'name':'Alan Varela','pos':'CDM','age':23,'rating':79,'nat':'Argentina'},
    {'name':'Nicolás González','pos':'CM','age':23,'rating':77,'nat':'Argentina'},
    {'name':'Mehdi Taremi','pos':'ST','age':31,'rating':82,'nat':'Iran'},
    {'name':'João Mário','pos':'CM','age':31,'rating':80,'nat':'Portugal'},
    {'name':'Zaidu Sanusi','pos':'RB','age':27,'rating':76,'nat':'Nigeria'},
    {'name':'Moussa Marega','pos':'ST','age':32,'rating':76,'nat':'Mali'},
    {'name':'Pepe','pos':'CB','age':42,'rating':77,'nat':'Portugal'},
    {'name':'Fábio Vieira','pos':'CAM','age':24,'rating':77,'nat':'Portugal'},
    {'name':'Mateus Uribe','pos':'CM','age':33,'rating':76,'nat':'Colombia'},
    {'name':'Victor Garcia','pos':'LB','age':21,'rating':70,'nat':'Spain'},
    {'name':'Wilson Manafá','pos':'RB','age':28,'rating':74,'nat':'Portugal'},
    {'name':'Malang Sarr','pos':'CB','age':26,'rating':74,'nat':'France'},
    {'name':'Diogo Costa','pos':'GK','age':25,'rating':84,'nat':'Portugal'},
    {'name':'Otávio','pos':'RW','age':30,'rating':82,'nat':'Portugal'},
    {'name':'Luis Diaz','pos':'LW','age':27,'rating':85,'nat':'Colombia'}
]

SPORTING_CP_PLAYERS = [
    {'name':'Antonio Adán','pos':'GK','age':38,'rating':78,'nat':'Spain'},
    {'name':'Vicente Guaita','pos':'GK','age':37,'rating':74,'nat':'Spain'},
    {'name':'Gonçalo Inácio','pos':'CB','age':24,'rating':81,'nat':'Portugal'},
    {'name':'Sebastián Coates','pos':'CB','age':34,'rating':80,'nat':'Uruguay'},
    {'name':'Ousmane Diomande','pos':'CB','age':21,'rating':80,'nat':'Ivory Coast'},
    {'name':'Ricardo Esgaio','pos':'RB','age':32,'rating':77,'nat':'Portugal'},
    {'name':'Nuno Santos','pos':'LW','age':30,'rating':81,'nat':'Portugal'},
    {'name':'Pedro Gonçalves','pos':'CAM','age':26,'rating':83,'nat':'Portugal'},
    {'name':'Hidemasa Morita','pos':'CM','age':29,'rating':80,'nat':'Japan'},
    {'name':'Viktor Gyökeres','pos':'ST','age':27,'rating':85,'nat':'Sweden'},
    {'name':'Gonzalo Plata','pos':'RW','age':24,'rating':74,'nat':'Ecuador'},
    {'name':'André','pos':'LB','age':25,'rating':73,'nat':'Portugal'},
    {'name':'Eduardo Quaresma','pos':'CB','age':21,'rating':71,'nat':'Portugal'},
    {'name':'Daniel Bragança','pos':'CM','age':24,'rating':73,'nat':'Portugal'},
    {'name':'Paulinho','pos':'CM','age':26,'rating':74,'nat':'Portugal'},
    {'name':'Pedro Porro','pos':'RB','age':25,'rating':79,'nat':'Spain'},
    {'name':'Gonçalo Inácio','pos':'CB','age':24,'rating':81,'nat':'Portugal'},
    {'name':'Antonio Adán','pos':'GK','age':38,'rating':78,'nat':'Spain'},
    {'name':'Jonathan','pos':'LB','age':20,'rating':69,'nat':'Brazil'},
    {'name':'Eustáquio','pos':'CM','age':28,'rating':72,'nat':'Portugal'},
    {'name':'Neto','pos':'CB','age':30,'rating':71,'nat':'Brazil'},
    {'name':'Babacar','pos':'ST','age':28,'rating':70,'nat':'Senegal'}
]

# ---------------------------
# Netherlands (20-22)
# ---------------------------

AJAX_PLAYERS = [
    {'name':'Diant Ramaj','pos':'GK','age':23,'rating':76,'nat':'Germany'},
    {'name':'Maarten Stekelenburg','pos':'GK','age':41,'rating':68,'nat':'Netherlands'},
    {'name':'Devyn Rensch','pos':'RB','age':22,'rating':77,'nat':'Netherlands'},
    {'name':'Jorrel Hato','pos':'CB','age':18,'rating':78,'nat':'Netherlands'},
    {'name':'Daley Blind','pos':'CB','age':34,'rating':73,'nat':'Netherlands'},
    {'name':'Jurrien Timber','pos':'CB','age':22,'rating':79,'nat':'Netherlands'},
    {'name':'Steven Bergwijn','pos':'LW','age':27,'rating':80,'nat':'Netherlands'},
    {'name':'Brian Brobbey','pos':'ST','age':23,'rating':81,'nat':'Netherlands'},
    {'name':'Noa Lang','pos':'RW','age':26,'rating':82,'nat':'Netherlands'},
    {'name':'Kenneth Taylor','pos':'CM','age':22,'rating':78,'nat':'Netherlands'},
    {'name':'Davy Klaassen','pos':'CM','age':31,'rating':76,'nat':'Netherlands'},
    {'name':'Sebastien Haller','pos':'ST','age':30,'rating':80,'nat':'Ivory Coast'},
    {'name':'Steven Berghuis','pos':'RW','age':33,'rating':81,'nat':'Netherlands'},
    {'name':'Jesper Karlsson','pos':'LW','age':25,'rating':78,'nat':'Sweden'},
    {'name':'Owen Wijndal','pos':'LB','age':23,'rating':76,'nat':'Netherlands'},
    {'name':'Edson Álvarez','pos':'CDM','age':26,'rating':82,'nat':'Mexico'},
    {'name':'Kasper Dolberg','pos':'ST','age':26,'rating':77,'nat':'Denmark'},
    {'name':'Mazin Ahmed','pos':'CB','age':21,'rating':70,'nat':'Netherlands'},
    {'name':'Dusan Tadic','pos':'CAM','age':36,'rating':78,'nat':'Serbia'},
    {'name':'Remko Pasveer','pos':'GK','age':39,'rating':70,'nat':'Netherlands'},
    {'name':'Jurrien Timber','pos':'CB','age':22,'rating':79,'nat':'Netherlands'},
    {'name':'Devyne Rensch','pos':'RB','age':22,'rating':77,'nat':'Netherlands'}
]

PSV_EINDHOVEN_PLAYERS = [
    {'name':'Walter Benítez','pos':'GK','age':32,'rating':80,'nat':'Argentina'},
    {'name':'Mauro Júnior','pos':'LB','age':26,'rating':75,'nat':'Brazil'},
    {'name':'Taylan Antalyali','pos':'CM','age':28,'rating':74,'nat':'Turkey'},
    {'name':'Joey Veerman','pos':'CM','age':27,'rating':82,'nat':'Netherlands'},
    {'name':'Noa Lang','pos':'LW','age':26,'rating':82,'nat':'Netherlands'},
    {'name':'Johan Bakayoko','pos':'RW','age':22,'rating':82,'nat':'Belgium'},
    {'name':'Luuk de Jong','pos':'ST','age':35,'rating':80,'nat':'Netherlands'},
    {'name':'Cody Gakpo','pos':'ST','age':25,'rating':83,'nat':'Netherlands'},
    {'name':'Sergiño Dest','pos':'RB','age':24,'rating':79,'nat':'USA'},
    {'name':'Olivier Boscagli','pos':'CB','age':28,'rating':79,'nat':'France'},
    {'name':'André Ramalho','pos':'CB','age':33,'rating':77,'nat':'Brazil'},
    {'name':'Ismael Saibari','pos':'CAM','age':24,'rating':79,'nat':'Morocco'},
    {'name':'Bruma','pos':'RW','age':28,'rating':78,'nat':'Portugal'},
    {'name':'Xavi Simons','pos':'CAM','age':20,'rating':78,'nat':'Netherlands'},
    {'name':'Sávio','pos':'ST','age':22,'rating':71,'nat':'Brazil'},
    {'name':'Joey Veerman','pos':'CM','age':27,'rating':82,'nat':'Netherlands'},
    {'name':'Noa Lang','pos':'LW','age':26,'rating':82,'nat':'Netherlands'},
    {'name':'Walter Benítez','pos':'GK','age':32,'rating':80,'nat':'Argentina'},
    {'name':'Yorbe Vertessen','pos':'RW','age':22,'rating':73,'nat':'Belgium'},
    {'name':'Ibrahim Sangaré','pos':'CDM','age':26,'rating':83,'nat':'Ivory Coast'},
    {'name':'Toni Lato','pos':'LB','age':26,'rating':74,'nat':'Spain'},
    {'name':'Mauro Júnior','pos':'LB','age':26,'rating':75,'nat':'Brazil'},
]

FEYENOORD_PLAYERS = [
    {'name':'Justin Bijlow','pos':'GK','age':27,'rating':81,'nat':'Netherlands'},
    {'name':'Lutsharel Geertruida','pos':'RB','age':25,'rating':82,'nat':'Netherlands'},
    {'name':'Gernot Trauner','pos':'CB','age':33,'rating':79,'nat':'Austria'},
    {'name':'David Hancko','pos':'CB','age':27,'rating':82,'nat':'Slovakia'},
    {'name':'Quilindschy Hartman','pos':'LB','age':23,'rating':78,'nat':'Netherlands'},
    {'name':'Mats Wieffer','pos':'CDM','age':25,'rating':81,'nat':'Netherlands'},
    {'name':'Calvin Stengs','pos':'RW','age':26,'rating':80,'nat':'Netherlands'},
    {'name':'Santiago Giménez','pos':'ST','age':24,'rating':84,'nat':'Mexico'},
    {'name':'Alireza Jahanbakhsh','pos':'RW','age':32,'rating':76,'nat':'Iran'},
    {'name':'Orkun Kökçü','pos':'CM','age':24,'rating':81,'nat':'Turkey'},
    {'name':'Ibrahim Dresevic','pos':'LB','age':25,'rating':71,'nat':'Sweden'},
    {'name':'Luis Sinisterra','pos':'LW','age':25,'rating':79,'nat':'Colombia'},
    {'name':'Tyrell Malacia','pos':'LB','age':26,'rating':76,'nat':'Netherlands'},
    {'name':'Frenkie de Jong','pos':'CM','age':27,'rating':86,'nat':'Netherlands'},
    {'name':'Jorrit Hendrix','pos':'CM','age':28,'rating':72,'nat':'Netherlands'},
    {'name':'Dylan Vente','pos':'ST','age':24,'rating':70,'nat':'Netherlands'},
    {'name':'Justin Kluivert','pos':'RW','age':25,'rating':74,'nat':'Netherlands'},
    {'name':'Gernot Trauner','pos':'CB','age':33,'rating':79,'nat':'Austria'},
    {'name':'Orkun Kökçü','pos':'CM','age':24,'rating':81,'nat':'Turkey'},
    {'name':'Santiago Giménez','pos':'ST','age':24,'rating':84,'nat':'Mexico'},
    {'name':'Justin Bijlow','pos':'GK','age':27,'rating':81,'nat':'Netherlands'}
]

# ---------------------------
# Belgium (23-24)
# ---------------------------

CLUB_BRUGGE_PLAYERS = [
    {'name':'Simon Mignolet','pos':'GK','age':36,'rating':75,'nat':'Belgium'},
    {'name':'Kris Torbensen','pos':'GK','age':22,'rating':68,'nat':'Belgium'},
    {'name':'Toni Leistner','pos':'CB','age':33,'rating':72,'nat':'Germany'},
    {'name':'Clinton Mata','pos':'RB','age':32,'rating':77,'nat':'Angola'},
    {'name':'Charles De Ketelaere','pos':'CAM','age':23,'rating':79,'nat':'Belgium'},
    {'name':'Noa Lang','pos':'RW','age':26,'rating':82,'nat':'Netherlands'},
    {'name':'Loïs Openda','pos':'ST','age':22,'rating':82,'nat':'Belgium'},
    {'name':'Victor Boniface','pos':'ST','age':21,'rating':80,'nat':'Nigeria'},
    {'name':'Ruud Vormer','pos':'CM','age':35,'rating':73,'nat':'Netherlands'},
    {'name':'Ruud Vormer','pos':'CM','age':35,'rating':73,'nat':'Netherlands'},
    {'name':'Ignace Van Der Brempt','pos':'RB','age':22,'rating':72,'nat':'Belgium'},
    {'name':'Casuais','pos':'CDM','age':28,'rating':71,'nat':'Belgium'},
    {'name':'Mateo Cassierra','pos':'ST','age':26,'rating':74,'nat':'Colombia'},
    {'name':'Davy Roef','pos':'GK','age':31,'rating':72,'nat':'Belgium'},
    {'name':'Eduard Sobol','pos':'LB','age':30,'rating':71,'nat':'Ukraine'},
    {'name':'Clinton Mata','pos':'RB','age':32,'rating':77,'nat':'Angola'},
    {'name':'Loïs Openda','pos':'ST','age':22,'rating':82,'nat':'Belgium'},
    {'name':'Faitout Maouassa','pos':'LB','age':27,'rating':73,'nat':'France'},
    {'name':'Noa Lang','pos':'RW','age':26,'rating':82,'nat':'Netherlands'},
    {'name':'Bas Dost','pos':'ST','age':35,'rating':68,'nat':'Netherlands'},
    {'name':'Gustaf','pos':'CM','age':20,'rating':68,'nat':'Sweden'},
    {'name':'D' 'G','pos':'CB','age':21,'rating':67,'nat':'Belgium'}
]

ANDERLECHT_PLAYERS = [
    {'name':'Ruddy Buquet','pos':'GK','age':34,'rating':70,'nat':'France'},
    {'name':'Sven Kums','pos':'CM','age':34,'rating':72,'nat':'Belgium'},
    {'name':'Matias Suarez','pos':'ST','age':35,'rating':71,'nat':'Argentina'},
    {'name':'Francis Amuzu','pos':'RW','age':23,'rating':72,'nat':'Belgium'},
    {'name':'Dante Vanzeir','pos':'ST','age':25,'rating':74,'nat':'Belgium'},
    {'name':'Josh Cullen','pos':'CM','age':28,'rating':72,'nat':'Ireland'},
    {'name':'Zeno Debast','pos':'CB','age':18,'rating':71,'nat':'Belgium'},
    {'name':'Paul Mukairu','pos':'RW','age':22,'rating':68,'nat':'Ghana'},
    {'name':'Anderlecht GK','pos':'GK','age':21,'rating':67,'nat':'Belgium'},
    {'name':'Michel-Ange Balikwisha','pos':'LW','age':21,'rating':72,'nat':'Belgium'},
    {'name':'Lior Refaelov','pos':'CAM','age':34,'rating':70,'nat':'Israel'},
    {'name':'Kumars','pos':'LB','age':23,'rating':68,'nat':'Belgium'},
    {'name':'Jovan','pos':'CB','age':24,'rating':69,'nat':'Serbia'},
    {'name':'Gerkens','pos':'CM','age':30,'rating':70,'nat':'Belgium'},
    {'name':'Danjuma','pos':'LW','age':27,'rating':74,'nat':'Netherlands'},
    {'name':'Sambi Lokonga','pos':'CM','age':24,'rating':76,'nat':'Belgium'},
    {'name':'Anderlecht Youth','pos':'SUB','age':19,'rating':66,'nat':'Belgium'},
    {'name':'Ramy','pos':'RB','age':26,'rating':70,'nat':'Egypt'},
    {'name':'Signeau','pos':'CB','age':28,'rating':69,'nat':'France'},
    {'name':'Anderlecht Coach','pos':'Coach','age':52,'rating':0,'nat':'Belgium'},
    {'name':'Iké Ugbo','pos':'ST','age':25,'rating':71,'nat':'Canada'},
    {'name':'Albert Sambi Lokonga','pos':'CM','age':24,'rating':76,'nat':'Belgium'}
]

# ---------------------------
# Turkey (25-26)
# ---------------------------

GALATASARAY_PLAYERS = [
    {'name':'Fernando Muslera','pos':'GK','age':37,'rating':78,'nat':'Uruguay'},
    {'name':'Inaki Pena','pos':'GK','age':26,'rating':73,'nat':'Spain'},
    {'name':'Sacha Boey','pos':'RB','age':23,'rating':73,'nat':'France'},
    {'name':'Victor Nelsson','pos':'CB','age':25,'rating':77,'nat':'Denmark'},
    {'name':'Marcao','pos':'CB','age':29,'rating':76,'nat':'Brazil'},
    {'name':'Sacha','pos':'LB','age':25,'rating':70,'nat':'France'},
    {'name':'Lucas Torreira','pos':'CM','age':28,'rating':78,'nat':'Uruguay'},
    {'name':'Kerem Aktürkoğlu','pos':'LW','age':25,'rating':79,'nat':'Turkey'},
    {'name':'Dries Mertens','pos':'ST','age':37,'rating':72,'nat':'Belgium'},
    {'name':'Mostafa Mohamed','pos':'ST','age':26,'rating':74,'nat':'Egypt'},
    {'name':'Aaron Boupendza','pos':'ST','age':26,'rating':72,'nat':'Gabon'},
    {'name':'Sofiane Feghouli','pos':'RW','age':33,'rating':72,'nat':'Algeria'},
    {'name':'Ryan Donk','pos':'CB','age':38,'rating':66,'nat':'Netherlands'},
    {'name':'Barış Alıcı','pos':'RW','age':27,'rating':68,'nat':'Turkey'},
    {'name':'Galatasaray Youth','pos':'SUB','age':19,'rating':65,'nat':'Turkey'},
    {'name':'Hakan Balta','pos':'Coach','age':40,'rating':0,'nat':'Turkey'},
    {'name':'Sacha','pos':'LB','age':25,'rating':70,'nat':'France'},
    {'name':'Omar Elabdellaoui','pos':'RB','age':33,'rating':71,'nat':'Norway'},
    {'name':'Emre Kılınç','pos':'RW','age':30,'rating':72,'nat':'Turkey'},
    {'name':'Younes Belhanda','pos':'CM','age':33,'rating':71,'nat':'Morocco'},
    {'name':'Babel','pos':'FW','age':36,'rating':70,'nat':'Netherlands'},
    {'name':'Sofiane','pos':'ST','age':24,'rating':72,'nat':'Algeria'}
]

FENERBAHCE_PLAYERS = [
    {'name':'Altay Bayındır','pos':'GK','age':27,'rating':79,'nat':'Turkey'},
    {'name':'Berke Özer','pos':'GK','age':23,'rating':70,'nat':'Turkey'},
    {'name':'Mert Hakan Yandaş','pos':'CM','age':30,'rating':75,'nat':'Turkey'},
    {'name':'İsmail Yüksek','pos':'CM','age':25,'rating':72,'nat':'Turkey'},
    {'name':'Willian Arão','pos':'CDM','age':33,'rating':75,'nat':'Brazil'},
    {'name':'Azedine Ounahi','pos':'CM','age':24,'rating':78,'nat':'Morocco'},
    {'name':'Enner Valencia','pos':'ST','age':35,'rating':78,'nat':'Ecuador'},
    {'name':'Serdar Dursun','pos':'ST','age':33,'rating':74,'nat':'Turkey'},
    {'name':'Mert Hakan','pos':'CM','age':30,'rating':75,'nat':'Turkey'},
    {'name':'Ferdi Kadıoğlu','pos':'RB','age':25,'rating':75,'nat':'Turkey'},
    {'name':'Gustavo','pos':'CB','age':29,'rating':74,'nat':'Brazil'},
    {'name':'Bright Osayi-Samuel','pos':'RW','age':25,'rating':77,'nat':'Nigeria'},
    {'name':'Zanka','pos':'CB','age':31,'rating':70,'nat':'Denmark'},
    {'name':'Serdar Aziz','pos':'CB','age':31,'rating':70,'nat':'Turkey'},
    {'name':'Miha Zajc','pos':'CAM','age':29,'rating':72,'nat':'Slovenia'},
    {'name':'İrfan Can Kahveci','pos':'CAM','age':27,'rating':76,'nat':'Turkey'},
    {'name':'Fenerbahce Youth','pos':'SUB','age':19,'rating':65,'nat':'Turkey'},
    {'name':'Pelkas','pos':'LW','age':28,'rating':72,'nat':'Greece'},
    {'name':'Mergim Berisha','pos':'ST','age':25,'rating':73,'nat':'Germany'},
    {'name':'Serdar','pos':'CM','age':28,'rating':71,'nat':'Turkey'},
    {'name':'Muhammed Gümüşkaya','pos':'CM','age':22,'rating':68,'nat':'Turkey'}
]

# ---------------------------
# Scotland (27-28)
# ---------------------------

CELTIC_PLAYERS = [
    {'name':'Joe Hart','pos':'GK','age':37,'rating':77,'nat':'England'},
    {'name':'Scott Bain','pos':'GK','age':32,'rating':73,'nat':'Scotland'},
    {'name':'Greg Taylor','pos':'LB','age':25,'rating':76,'nat':'Scotland'},
    {'name':'Alistair Johnston','pos':'RB','age':26,'rating':74,'nat':'Canada'},
    {'name':'Cameron Carter-Vickers','pos':'CB','age':26,'rating':78,'nat':'USA'},
    {'name':'Carl Starfelt','pos':'CB','age':27,'rating':76,'nat':'Sweden'},
    {'name':'Stephen Welsh','pos':'CB','age':22,'rating':72,'nat':'Scotland'},
    {'name':'Matt O’Riley','pos':'CM','age':22,'rating':77,'nat':'Denmark'},
    {'name':'Callum McGregor','pos':'CM','age':30,'rating':81,'nat':'Scotland'},
    {'name':'Reo Hatate','pos':'CM','age':25,'rating':77,'nat':'Japan'},
    {'name':'David Turnbull','pos':'AM','age':22,'rating':73,'nat':'Scotland'},
    {'name':'Kyogo Furuhashi','pos':'ST','age':28,'rating':82,'nat':'Japan'},
    {'name':'James Forrest','pos':'RW','age':31,'rating':74,'nat':'Scotland'},
    {'name':'Jota','pos':'LW','age':28,'rating':77,'nat':'Portugal'},
    {'name':'Liel Abada','pos':'LW','age':22,'rating':75,'nat':'Israel'},
    {'name':'Mikey Johnston','pos':'RW','age':24,'rating':71,'nat':'Republic of Ireland'},
    {'name':'Carl','pos':'CB','age':21,'rating':69,'nat':'Scotland'},
    {'name':'Joe Hart','pos':'GK','age':37,'rating':77,'nat':'England'},
    {'name':'Celtic Youth','pos':'SUB','age':19,'rating':66,'nat':'Scotland'},
    {'name':'Liam Scales','pos':'CB','age':25,'rating':72,'nat':'Ireland'},
    {'name':'Cameron Carter-Vickers','pos':'CB','age':26,'rating':78,'nat':'USA'},
    {'name':'James McCarthy','pos':'CM','age':33,'rating':70,'nat':'Republic of Ireland'}
]

RANGERS_PLAYERS = [
    {'name':'Allan McGregor','pos':'GK','age':41,'rating':72,'nat':'Scotland'},
    {'name':'Jon McLaughlin','pos':'GK','age':36,'rating':70,'nat':'Scotland'},
    {'name':'James Tavernier','pos':'RB','age':32,'rating':81,'nat':'England'},
    {'name':'Filip Helander','pos':'CB','age':30,'rating':74,'nat':'Sweden'},
    {'name':'Connor Goldson','pos':'CB','age':30,'rating':77,'nat':'England'},
    {'name':'John Souttar','pos':'CB','age':27,'rating':75,'nat':'Scotland'},
    {'name':'Ryan Jack','pos':'CM','age':29,'rating':74,'nat':'Scotland'},
    {'name':'Glen Kamara','pos':'CM','age':27,'rating':76,'nat':'Finland'},
    {'name':'Scott Arfield','pos':'CM','age':33,'rating':72,'nat':'Canada'},
    {'name':'Joe Aribo','pos':'RW','age':26,'rating':76,'nat':'Nigeria'},
    {'name':'Rangers Youth','pos':'SUB','age':19,'rating':66,'nat':'Scotland'},
    {'name':'Glen Kamara','pos':'CM','age':27,'rating':76,'nat':'Finland'},
    {'name':'Fashion Sakala','pos':'RW','age':27,'rating':74,'nat':'Zambia'},
    {'name':'Antonio Colak','pos':'ST','age':31,'rating':73,'nat':'Croatia'},
    {'name':'Scott Wright','pos':'LW','age':25,'rating':71,'nat':'Scotland'},
    {'name':'Niko Katic','pos':'CB','age':28,'rating':70,'nat':'Croatia'},
    {'name':'James Tavernier','pos':'RB','age':32,'rating':81,'nat':'England'},
    {'name':'Allan McGregor','pos':'GK','age':41,'rating':72,'nat':'Scotland'},
    {'name':'Rangers Coach','pos':'Coach','age':50,'rating':0,'nat':'Northern Ireland'},
    {'name':'Ridvan Yilmaz','pos':'LB','age':22,'rating':74,'nat':'Turkey'},
    {'name':'Borna Barišić','pos':'LB','age':30,'rating':73,'nat':'Croatia'},
    {'name':'David Bates','pos':'CB','age':25,'rating':70,'nat':'Scotland'}
]

# ---------------------------
# Austria (29)
# ---------------------------

RB_SALZBURG_PLAYERS = [
    {'name':'Alexander Walke','pos':'GK','age':38,'rating':73,'nat':'Germany'},
    {'name':'Benjamin Šeško','pos':'ST','age':19,'rating':77,'nat':'Slovenia'},
    {'name':'Max Wöber','pos':'CB','age':26,'rating':76,'nat':'Austria'},
    {'name':'Rasmus Kristensen','pos':'RB','age':25,'rating':76,'nat':'Denmark'},
    {'name':'Mohamed Camara','pos':'CDM','age':23,'rating':80,'nat':'Mali'},
    {'name':'Mërgim Berisha','pos':'ST','age':25,'rating':73,'nat':'Germany'},
    {'name':'Sékou Koïta','pos':'RW','age':23,'rating':78,'nat':'Mali'},
    {'name':'Brenden Aaronson','pos':'RW','age':23,'rating':78,'nat':'USA'},
    {'name':'Noah Okafor','pos':'ST','age':25,'rating':79,'nat':'Switzerland'},
    {'name':'Maximilian Wöber','pos':'CB','age':26,'rating':76,'nat':'Austria'},
    {'name':'Andi Ulmer','pos':'LB','age':34,'rating':68,'nat':'Austria'},
    {'name':'Salzburg Youth','pos':'SUB','age':19,'rating':65,'nat':'Austria'},
    {'name':'Benjamin Šeško','pos':'ST','age':19,'rating':77,'nat':'Slovenia'},
    {'name':'Ethan Ampadu','pos':'CB','age':22,'rating':75,'nat':'Wales'},
    {'name':'Mladen','pos':'CM','age':24,'rating':70,'nat':'Croatia'},
    {'name':'Patson Daka','pos':'ST','age':25,'rating':78,'nat':'Zambia'},
    {'name':'Karim Adeyemi','pos':'ST','age':23,'rating':81,'nat':'Germany'},
    {'name':'Salzburg Coach','pos':'Coach','age':48,'rating':0,'nat':'Austria'}
]

# ---------------------------
# Ukraine (30)
# ---------------------------

SHAKHTAR_DONETSK_PLAYERS = [
    {'name':'Andriy Pyatov','pos':'GK','age':40,'rating':72,'nat':'Ukraine'},
    {'name':'Anatoliy Trubin','pos':'GK','age':22,'rating':81,'nat':'Ukraine'},
    {'name':'Taras Stepanenko','pos':'CDM','age':33,'rating':75,'nat':'Ukraine'},
    {'name':'Marcos Antonio','pos':'CDM','age':25,'rating':78,'nat':'Brazil'},
    {'name':'Mykhailo Mudryk','pos':'LW','age':21,'rating':80,'nat':'Ukraine'},
    {'name':'Wesley','pos':'ST','age':30,'rating':78,'nat':'Brazil'},
    {'name':'Júnior Moraes','pos':'ST','age':35,'rating':70,'nat':'Brazil'},
    {'name':'Dodo','pos':'RB','age':25,'rating':74,'nat':'Brazil'},
    {'name':'Olarenwaju Kayode','pos':'ST','age':30,'rating':71,'nat':'Nigeria'},
    {'name':'Ismaily','pos':'LB','age':32,'rating':72,'nat':'Brazil'},
    {'name':'Marcos Antonio','pos':'CM','age':25,'rating':78,'nat':'Brazil'},
    {'name':'Shakhtar Youth','pos':'SUB','age':19,'rating':65,'nat':'Ukraine'},
    {'name':'Taison','pos':'AM','age':36,'rating':71,'nat':'Brazil'},
    {'name':'Alan Patrick','pos':'CM','age':33,'rating':72,'nat':'Brazil'},
    {'name':'Sydorchuk','pos':'CM','age':31,'rating':72,'nat':'Ukraine'},
    {'name':'Marcelinho','pos':'RW','age':28,'rating':74,'nat':'Brazil'},
    {'name':'Fred','pos':'CM','age':30,'rating':78,'nat':'Brazil'},
    {'name':'Mykola Matviyenko','pos':'LB','age':26,'rating':74,'nat':'Ukraine'},
    {'name':'Heorhiy Sudakov','pos':'CM','age':21,'rating':74,'nat':'Belarus'},
    {'name':'Shakhtar Coach','pos':'Coach','age':50,'rating':0,'nat':'Portugal'}
]

# ---------------------------
# Switzerland (31)
# ---------------------------

YOUNG_BOYS_PLAYERS = [
    {'name':'Anthony Racioppi','pos':'GK','age':25,'rating':74,'nat':'Switzerland'},
    {'name':'David von Ballmoos','pos':'GK','age':29,'rating':75,'nat':'Switzerland'},
    {'name':'Jordan Siebatcheu','pos':'ST','age':28,'rating':78,'nat':'USA'},
    {'name':'Jean-Pierre Nsame','pos':'ST','age':29,'rating':80,'nat':'Cameroon'},
    {'name':'Christian Fassnacht','pos':'RW','age':29,'rating':77,'nat':'Switzerland'},
    {'name':'Theoson Siebatcheu','pos':'ST','age':27,'rating':76,'nat':'USA'},
    {'name':'Michel Aebischer','pos':'CM','age':26,'rating':76,'nat':'Switzerland'},
    {'name':'Silvan Widmer','pos':'RB','age':29,'rating':75,'nat':'Switzerland'},
    {'name':'Jordan Lotomba','pos':'LB','age':25,'rating':75,'nat':'Switzerland'},
    {'name':'Sandro Lauper','pos':'CM','age':24,'rating':74,'nat':'Switzerland'},
    {'name':'Young Boys Youth','pos':'SUB','age':19,'rating':65,'nat':'Switzerland'}
]

# ---------------------------
# Serbia (32)
# ---------------------------

RED_STAR_BELGRADE_PLAYERS = [
    {'name':'Milan Borjan','pos':'GK','age':36,'rating':75,'nat':'Canada/Serbia'},
    {'name':'Predrag Rajković','pos':'GK','age':28,'rating':74,'nat':'Serbia'},
    {'name':'Aleksandar Katai','pos':'RW','age':33,'rating':72,'nat':'Serbia'},
    {'name':'El Fardou Ben','pos':'ST','age':33,'rating':73,'nat':'Cape Verde'},
    {'name':'Milica','pos':'CB','age':25,'rating':72,'nat':'Serbia'},
    {'name':'Milunović','pos':'CB','age':30,'rating':71,'nat':'Serbia'},
    {'name':'Ben','pos':'LW','age':24,'rating':70,'nat':'Portugal'},
    {'name':'Red Star Youth','pos':'SUB','age':19,'rating':65,'nat':'Serbia'},
    {'name':'Milan Pavkov','pos':'ST','age':28,'rating':73,'nat':'Serbia'},
    {'name':'El Fardou Ben','pos':'ST','age':33,'rating':73,'nat':'Cape Verde'},
    {'name':'Goran Causic','pos':'CM','age':27,'rating':71,'nat':'Serbia'},
    {'name':'Red Star Coach','pos':'Coach','age':54,'rating':0,'nat':'Serbia'}
]

# ---------------------------
# EUROPA LEAGUE (32 teams) - NO ENGLISH CLUBS
# ---------------------------
# Spain (Real Sociedad, Villarreal, Real Betis, Athletic Bilbao)
REAL_SOCIEDAD_PLAYERS = [
    {'name':'Álex Remiro','pos':'GK','age':30,'rating':76,'nat':'Spain'},
    {'name':'Andoni Zubizarreta','pos':'GK','age':20,'rating':67,'nat':'Spain'},
    {'name':'Robin Le Normand','pos':'CB','age':26,'rating':81,'nat':'Spain'},
    {'name':'Igor Zubeldia','pos':'CM','age':26,'rating':78,'nat':'Spain'},
    {'name':'Mikel Oyarzabal','pos':'LW','age':26,'rating':84,'nat':'Spain'},
    {'name':'Takefusa Kubo','pos':'RW','age':22,'rating':82,'nat':'Japan'},
    {'name':'Alexander Sorloth','pos':'ST','age':27,'rating':78,'nat':'Norway'},
    {'name':'Aihen Muñoz','pos':'LB','age':25,'rating':73,'nat':'Spain'},
    {'name':'Guruzeta','pos':'ST','age':22,'rating':70,'nat':'Spain'},
    {'name':'Real Sociedad Youth','pos':'SUB','age':19,'rating':65,'nat':'Spain'},
    {'name':'Mikel Merino','pos':'CM','age':28,'rating':80,'nat':'Spain'},
    {'name':'Robin Le Normand','pos':'CB','age':26,'rating':81,'nat':'Spain'},
    {'name':'Diego Rico','pos':'LB','age':31,'rating':72,'nat':'Spain'},
    {'name':'Jon Pacheco','pos':'CB','age':22,'rating':74,'nat':'Spain'},
    {'name':'Nacho Monreal','pos':'LB','age':36,'rating':68,'nat':'Spain'},
    {'name':'Mikel Oyarzabal','pos':'LW','age':26,'rating':84,'nat':'Spain'},
    {'name':'David Silva','pos':'CAM','age':37,'rating':74,'nat':'Spain'},
    {'name':'Alexander Sorloth','pos':'ST','age':27,'rating':78,'nat':'Norway'},
    {'name':'Adnan Januzaj','pos':'RW','age':29,'rating':74,'nat':'Belgium'},
    {'name':'Theo Bongonda','pos':'RW','age':27,'rating':72,'nat':'Belgium'},
    {'name':'Ander Barrenetxea','pos':'LW','age':21,'rating':73,'nat':'Spain'},
    {'name':'Aihen Muñoz','pos':'LB','age':25,'rating':73,'nat':'Spain'}
]

VILLARREAL_PLAYERS = [
    {'name':'Gerónimo Rulli','pos':'GK','age':32,'rating':80,'nat':'Argentina'},
    {'name':'Sergio Asenjo','pos':'GK','age':34,'rating':74,'nat':'Spain'},
    {'name':'Pau Torres','pos':'CB','age':25,'rating':80,'nat':'Spain'},
    {'name':'Raúl Albiol','pos':'CB','age':38,'rating':72,'nat':'Spain'},
    {'name':'Alfonso Pedraza','pos':'LB','age':27,'rating':76,'nat':'Spain'},
    {'name':'Juan Foyth','pos':'CB','age':25,'rating':76,'nat':'Argentina'},
    {'name':'Dani Parejo','pos':'CM','age':34,'rating':79,'nat':'Spain'},
    {'name':'Yéremy Pino','pos':'RW','age':21,'rating':77,'nat':'Spain'},
    {'name':'Arnaut Danjuma','pos':'LW','age':26,'rating':78,'nat':'Netherlands'},
    {'name':'Boulaye Dia','pos':'ST','age':26,'rating':77,'nat':'Senegal'},
    {'name':'Gerard Moreno','pos':'ST','age':30,'rating':83,'nat':'Spain'},
    {'name':'Moi Gómez','pos':'CAM','age':29,'rating':74,'nat':'Spain'},
    {'name':'Etienne Capoue','pos':'CDM','age':33,'rating':75,'nat':'France'},
    {'name':'Yeremy Pino','pos':'RW','age':21,'rating':77,'nat':'Spain'},
    {'name':'Juan Foyth','pos':'CB','age':25,'rating':76,'nat':'Argentina'},
    {'name':'Villarreal Youth','pos':'SUB','age':19,'rating':65,'nat':'Spain'}
]

REAL_BETIS_PLAYERS = [
    {'name':'Rui Silva','pos':'GK','age':30,'rating':80,'nat':'Portugal'},
    {'name':'Joel Robles','pos':'GK','age':34,'rating':72,'nat':'Spain'},
    {'name':'Álex Moreno','pos':'LB','age':30,'rating':78,'nat':'Spain'},
    {'name':'Marc Bartra','pos':'CB','age':32,'rating':76,'nat':'Spain'},
    {'name':'Germán Pezzella','pos':'CB','age':33,'rating':75,'nat':'Argentina'},
    {'name':'William Carvalho','pos':'CDM','age':30,'rating':79,'nat':'Portugal'},
    {'name':'Sergio Canales','pos':'CAM','age':32,'rating':82,'nat':'Spain'},
    {'name':'Nabil Fekir','pos':'CAM','age':29,'rating':81,'nat':'France'},
    {'name':'Borja Iglesias','pos':'ST','age':29,'rating':80,'nat':'Spain'},
    {'name':'Joaquín','pos':'RW','age':40,'rating':65,'nat':'Spain'},
    {'name':'Juanmi','pos':'ST','age':30,'rating':74,'nat':'Spain'},
    {'name':'Ayoze Pérez','pos':'RW','age':30,'rating':76,'nat':'Spain'},
    {'name':'Gonzalo Montiel','pos':'RB','age':28,'rating':78,'nat':'Argentina'},
    {'name':'Real Betis Youth','pos':'SUB','age':19,'rating':65,'nat':'Spain'}
]

ATHLETIC_BILBAO_PLAYERS = [
    {'name':'Unai Simón','pos':'GK','age':27,'rating':82,'nat':'Spain'},
    {'name':'Iago Herrerín','pos':'GK','age':34,'rating':70,'nat':'Spain'},
    {'name':'Iker Muniain','pos':'RW','age':30,'rating':78,'nat':'Spain'},
    {'name':'Iñaki Williams','pos':'ST','age':29,'rating':82,'nat':'Ghana'},
    {'name':'Inaki Williams','pos':'ST','age':29,'rating':82,'nat':'Spain'},
    {'name':'Yeray Álvarez','pos':'CB','age':26,'rating':76,'nat':'Spain'},
    {'name':'Yeray','pos':'CB','age':26,'rating':76,'nat':'Spain'},
    {'name':'Iñigo Martinez','pos':'CB','age':33,'rating':80,'nat':'Spain'},
    {'name':'Unai Núñez','pos':'CB','age':25,'rating':73,'nat':'Spain'},
    {'name':'Mikel Vesga','pos':'CM','age':30,'rating':72,'nat':'Spain'},
    {'name':'Mikel Balenziaga','pos':'LB','age':33,'rating':70,'nat':'Spain'},
    {'name':'Asier Villalibre','pos':'ST','age':26,'rating':72,'nat':'Spain'},
    {'name':'Capa','pos':'RB','age':30,'rating':72,'nat':'Spain'},
    {'name':'Athletic Youth','pos':'SUB','age':19,'rating':65,'nat':'Spain'}
]

# ---------------------------
# Germany (Eintracht, Union, Freiburg, Hoffenheim)
# ---------------------------

EINTRACHT_FRANKFURT_PLAYERS = [
    {'name':'Kevin Trapp','pos':'GK','age':33,'rating':82,'nat':'Germany'},
    {'name':'Alfred Duncan','pos':'CM','age':30,'rating':74,'nat':'Ghana'},
    {'name':'Jesper Lindstrøm','pos':'RW','age':23,'rating':78,'nat':'Denmark'},
    {'name':'Rafael Borré','pos':'ST','age':28,'rating':77,'nat':'Colombia'},
    {'name':'Daichi Kamada','pos':'AM','age':26,'rating':78,'nat':'Japan'},
    {'name':'Makoto Hasebe','pos':'CM','age':38,'rating':70,'nat':'Japan'},
    {'name':'Evan N\'Dicka','pos':'CB','age':22,'rating':77,'nat':'France'},
    {'name':'Tuta','pos':'CB','age':24,'rating':74,'nat':'Brazil'},
    {'name':'Sebastien Haller','pos':'ST','age':30,'rating':80,'nat':'Ivory Coast'},
    {'name':'Eddie Salcedo','pos':'ST','age':22,'rating':72,'nat':'Italy'},
    {'name':'Eintracht Youth','pos':'SUB','age':19,'rating':65,'nat':'Germany'}
]

UNION_BERLIN_PLAYERS = [
    {'name':'André Silva','pos':'ST','age':28,'rating':82,'nat':'Portugal'},
    {'name':'Timo Baumgartl','pos':'CB','age':28,'rating':74,'nat':'Germany'},
    {'name':'Christopher Trimmel','pos':'RB','age':36,'rating':70,'nat':'Austria'},
    {'name':'Niko Gießelmann','pos':'LB','age':33,'rating':71,'nat':'Germany'},
    {'name':'Max Kruse','pos':'ST','age':34,'rating':72,'nat':'Germany'},
    {'name':'Taiwo Awoniyi','pos':'ST','age':25,'rating':78,'nat':'Nigeria'},
    {'name':'Grischa Prömel','pos':'CM','age':29,'rating':72,'nat':'Germany'},
    {'name':'Union Youth','pos':'SUB','age':19,'rating':65,'nat':'Germany'}
]

SC_FREIBURG_PLAYERS = [
    {'name':'Mark Flekken','pos':'GK','age':30,'rating':77,'nat':'Netherlands'},
    {'name':'Nicolas Höfler','pos':'CM','age':31,'rating':73,'nat':'Germany'},
    {'name':'Christian Günter','pos':'LB','age':29,'rating':76,'nat':'Germany'},
    {'name':'Pascal Stenzel','pos':'RB','age':26,'rating':73,'nat':'Germany'},
    {'name':'Christian Streich','pos':'Coach','age':66,'rating':0,'nat':'Germany'},
    {'name':'Roland Sallai','pos':'RW','age':25,'rating':77,'nat':'Hungary'},
    {'name':'Lucas Höler','pos':'ST','age':29,'rating':76,'nat':'Germany'},
    {'name':'Kevin Schade','pos':'LW','age':22,'rating':75,'nat':'Germany'},
    {'name':'Freiburg Youth','pos':'SUB','age':18,'rating':65,'nat':'Germany'}
]

TSG_HOFFENHEIM_PLAYERS = [
    {'name':'Oliver Baumann','pos':'GK','age':33,'rating':80,'nat':'Germany'},
    {'name':'Kevin Vogt','pos':'CB','age':31,'rating':74,'nat':'Germany'},
    {'name':'Dennis Geiger','pos':'CM','age':26,'rating':75,'nat':'Germany'},
    {'name':'Andrej Kramarić','pos':'ST','age':32,'rating':81,'nat':'Croatia'},
    {'name':'Ihlas Bebou','pos':'RW','age':28,'rating':76,'nat':'Togo'},
    {'name':'Chris Führich','pos':'LW','age':24,'rating':75,'nat':'Germany'},
    {'name':'Hoffenheim Youth','pos':'SUB','age':19,'rating':65,'nat':'Germany'}
]

# ---------------------------
# Italy (Roma, Lazio, Atalanta, Fiorentina)
# ---------------------------

AS_ROMA_PLAYERS = [
    {'name':'Rui Patrício','pos':'GK','age':36,'rating':82,'nat':'Portugal'},
    {'name':'Pau López','pos':'GK','age':30,'rating':80,'nat':'Spain'},
    {'name':'Gianluca Mancini','pos':'CB','age':27,'rating':80,'nat':'Italy'},
    {'name':'Chris Smalling','pos':'CB','age':33,'rating':76,'nat':'England'},
    {'name':'Marash Kumbulla','pos':'CB','age':22,'rating':73,'nat':'Albania'},
    {'name':'Lorenzo Pellegrini','pos':'CM','age':27,'rating':83,'nat':'Italy'},
    {'name':'Nicolo Zaniolo','pos':'AM','age':24,'rating':79,'nat':'Italy'},
    {'name':'Paulo Dybala','pos':'FW','age':30,'rating':84,'nat':'Argentina'},
    {'name':'Romelu Lukaku','pos':'ST','age':30,'rating':86,'nat':'Belgium'},
    {'name':'Tammy Abraham','pos':'ST','age':26,'rating':80,'nat':'England'},
    {'name':'AS Roma Youth','pos':'SUB','age':19,'rating':65,'nat':'Italy'}
]

LAZIO_PLAYERS = [
    {'name':'Ivan Provedel','pos':'GK','age':29,'rating':78,'nat':'Italy'},
    {'name':'Thomas Strakosha','pos':'GK','age':29,'rating':73,'nat':'Albania'},
    {'name':'Gonzalo Escalante','pos':'CM','age':30,'rating':72,'nat':'Argentina'},
    {'name':'Sergej Milinković-Savić','pos':'CM','age':28,'rating':84,'nat':'Serbia'},
    {'name':'Ciro Immobile','pos':'ST','age':33,'rating':85,'nat':'Italy'},
    {'name':'Felipe Anderson','pos':'RW','age':30,'rating':78,'nat':'Brazil'},
    {'name':'Lazio Youth','pos':'SUB','age':19,'rating':65,'nat':'Italy'}
]

ATALANTA_PLAYERS = [
    {'name':'Marco Sportiello','pos':'GK','age':33,'rating':76,'nat':'Italy'},
    {'name':'Ederson','pos':'GK','age':29,'rating':75,'nat':'Brazil'},
    {'name':'Teun Koopmeiners','pos':'CM','age':25,'rating':81,'nat':'Netherlands'},
    {'name':'Ruslan Malinovskyi','pos':'AM','age':28,'rating':78,'nat':'Ukraine'},
    {'name':'Duván Zapata','pos':'ST','age':31,'rating':79,'nat':'Colombia'},
    {'name':'Gianluca Scamacca','pos':'ST','age':25,'rating':78,'nat':'Italy'},
    {'name':'Atalanta Youth','pos':'SUB','age':19,'rating':65,'nat':'Italy'}
]

FIORENTINA_PLAYERS = [
    {'name':'Pietro Terracciano','pos':'GK','age':33,'rating':72,'nat':'Italy'},
    {'name':'Bartłomiej Drągowski','pos':'GK','age':26,'rating':75,'nat':'Poland'},
    {'name':'Nicolò Zaniolo','pos':'AM','age':24,'rating':79,'nat':'Italy'},
    {'name':'Dusan Vlahovic','pos':'ST','age':25,'rating':85,'nat':'Serbia'},
    {'name':'Giovanni Simeone','pos':'ST','age':30,'rating':79,'nat':'Argentina'},
    {'name':'Fiorentina Youth','pos':'SUB','age':19,'rating':65,'nat':'Italy'}
]

# ---------------------------
# France (Lille, Nice, Rennes, Lens)
# ---------------------------

LILLE_PLAYERS = [
    {'name':'Illan Meslier','pos':'GK','age':24,'rating':80,'nat':'France'},
    {'name':'Jonathan David','pos':'ST','age':24,'rating':82,'nat':'Canada'},
    {'name':'Gabriel Magalhães','pos':'CB','age':25,'rating':82,'nat':'Brazil'},
    {'name':'Yusuf Yazıcı','pos':'AM','age':27,'rating':76,'nat':'Turkey'},
    {'name':'Lille Youth','pos':'SUB','age':19,'rating':65,'nat':'France'}
]

NICE_PLAYERS = [
    {'name':'Walter Benítez','pos':'GK','age':32,'rating':80,'nat':'Argentina'},
    {'name':'Khephren Thuram','pos':'CM','age':22,'rating':75,'nat':'France'},
    {'name':'Gonçalo Guedes','pos':'RW','age':27,'rating':78,'nat':'Portugal'},
    {'name':'Amine Gouiri','pos':'ST','age':23,'rating':78,'nat':'France'},
    {'name':'Nice Youth','pos':'SUB','age':19,'rating':65,'nat':'France'}
]

RENNES_PLAYERS = [
    {'name':'Alban Lafont','pos':'GK','age':24,'rating':79,'nat':'France'},
    {'name':'Flavien Tait','pos':'RW','age':31,'rating':73,'nat':'France'},
    {'name':'Martin Terrier','pos':'ST','age':25,'rating':77,'nat':'France'},
    {'name':'Rennes Youth','pos':'SUB','age':19,'rating':65,'nat':'France'}
]

LENS_PLAYERS = [
    {'name':'Brice Samba','pos':'GK','age':30,'rating':75,'nat':'DR Congo'},
    {'name':'Seko Fofana','pos':'CM','age':28,'rating':80,'nat':'Ivory Coast'},
    {'name':'Jonathan David','pos':'ST','age':24,'rating':82,'nat':'Canada'},
    {'name':'Lens Youth','pos':'SUB','age':19,'rating':65,'nat':'France'}
]

# ---------------------------
# Portugal (Braga, Vitória, Rio Ave)
# ---------------------------

BRAGA_PLAYERS = [
    {'name':'Matheus','pos':'GK','age':26,'rating':73,'nat':'Brazil'},
    {'name':'Paulinho','pos':'ST','age':28,'rating':78,'nat':'Portugal'},
    {'name':'Braga Youth','pos':'SUB','age':19,'rating':65,'nat':'Portugal'}
]

VITORIA_GUIMARAES_PLAYERS = [
    {'name':'Miguel Oliveira','pos':'GK','age':25,'rating':72,'nat':'Portugal'},
    {'name':'Hugo Cunha','pos':'ST','age':23,'rating':72,'nat':'Portugal'},
    {'name':'Vitoria Youth','pos':'SUB','age':19,'rating':65,'nat':'Portugal'}
]

RIO_AVE_PLAYERS = [
    {'name':'Jose Sa','pos':'GK','age':34,'rating':75,'nat':'Portugal'},
    {'name':'Rio Ave Youth','pos':'SUB','age':19,'rating':65,'nat':'Portugal'}
]

# ---------------------------
# Netherlands (AZ, Twente, Utrecht)
# ---------------------------

AZ_ALKMAAR_PLAYERS = [
    {'name':'Mathew Ryan','pos':'GK','age':31,'rating':79,'nat':'Australia'},
    {'name':'Teun Koopmeiners','pos':'CM','age':25,'rating':81,'nat':'Netherlands'},
    {'name':'AZ Youth','pos':'SUB','age':19,'rating':65,'nat':'Netherlands'}
]

FC_TWENTE_PLAYERS = [
    {'name':'Daniël de Ridder','pos':'Coach','age':40,'rating':0,'nat':'Netherlands'},
    {'name':'FC Twente Youth','pos':'SUB','age':19,'rating':65,'nat':'Netherlands'}
]

FC_UTRECHT_PLAYERS = [
    {'name':'Maarten Paes','pos':'GK','age':25,'rating':73,'nat':'Netherlands'},
    {'name':'FC Utrecht Youth','pos':'SUB','age':19,'rating':65,'nat':'Netherlands'}
]

# ---------------------------
# Belgium (Genk, Royal Antwerp)
# ---------------------------

GENK_PLAYERS = [
    {'name':'Maarten Vandevoordt','pos':'GK','age':20,'rating':76,'nat':'Belgium'},
    {'name':'Theo Bongonda','pos':'RW','age':27,'rating':72,'nat':'Belgium'},
    {'name':'Genk Youth','pos':'SUB','age':19,'rating':65,'nat':'Belgium'}
]

ROYAL_ANTWERP_PLAYERS = [
    {'name':'Jean Butez','pos':'GK','age':27,'rating':73,'nat':'France'},
    {'name':'Felipe Pardo','pos':'RW','age':32,'rating':71,'nat':'Colombia'},
    {'name':'Royal Antwerp Youth','pos':'SUB','age':19,'rating':65,'nat':'Belgium'}
]

# ---------------------------
# Greece (Olympiacos, Panathinaikos)
# ---------------------------

OLYMPIACOS_PLAYERS = [
    {'name':'José Sá','pos':'GK','age':30,'rating':80,'nat':'Portugal'},
    {'name':'Youssef El-Arabi','pos':'ST','age':35,'rating':75,'nat':'Morocco'},
    {'name':'Olympiacos Youth','pos':'SUB','age':19,'rating':65,'nat':'Greece'}
]

PANATHINAIKOS_PLAYERS = [
    {'name':'Sokratis Dioudis','pos':'GK','age':29,'rating':73,'nat':'Greece'},
    {'name':'Djibril Sow','pos':'CM','age':27,'rating':77,'nat':'Switzerland'},
    {'name':'Panathinaikos Youth','pos':'SUB','age':19,'rating':65,'nat':'Greece'}
]

# ---------------------------
# Czech Republic (Slavia Prague)
# ---------------------------

SLAVIA_PRAGUE_PLAYERS = [
    {'name':'Ondřej Kolář','pos':'GK','age':27,'rating':75,'nat':'Czech Republic'},
    {'name':'Lukas Provod','pos':'RW','age':25,'rating':72,'nat':'Czech Republic'},
    {'name':'Slavia Youth','pos':'SUB','age':19,'rating':65,'nat':'Czech Republic'}
]

# ---------------------------
# Ukraine (Dynamo Kyiv)
# ---------------------------

DYNAMO_KYIV_PLAYERS = [
    {'name':'Heorhiy Bushchan','pos':'GK','age':27,'rating':75,'nat':'Ukraine'},
    {'name':'Dynamo Youth','pos':'SUB','age':19,'rating':65,'nat':'Ukraine'}
]

# ---------------------------
# Denmark (Copenhagen)
# ---------------------------

COPENHAGEN_PLAYERS = [
    {'name':'Kamil Grabara','pos':'GK','age':25,'rating':77,'nat':'Poland'},
    {'name':'Lukas Lerager','pos':'CM','age':30,'rating':74,'nat':'Denmark'},
    {'name':'Copenhagen Youth','pos':'SUB','age':19,'rating':65,'nat':'Denmark'}
]

# ---------------------------
# Norway (Bodø/Glimt)
# ---------------------------

BODO_GLIMT_PLAYERS = [
    {'name':'Joshua Smits','pos':'GK','age':27,'rating':72,'nat':'Netherlands'},
    {'name':'Patrick Berg','pos':'CM','age':25,'rating':75,'nat':'Norway'},
    {'name':'Erling Haaland','pos':'ST','age':19,'rating':78,'nat':'Norway'},  # historical note
    {'name':'Bodo Youth','pos':'SUB','age':19,'rating':65,'nat':'Norway'}
]

# ---------------------------
# Israel (Maccabi Haifa)
# ---------------------------

MACCABI_HAIFA_PLAYERS = [
    {'name':'Dacosta','pos':'GK','age':27,'rating':73,'nat':'Israel'},
    {'name':'Maccabi Youth','pos':'SUB','age':19,'rating':65,'nat':'Israel'}
]

# ---------------------------
# Cyprus (APOEL)
# ---------------------------

APOEL_PLAYERS = [
    {'name':'Dusan Shch', 'pos':'GK','age':30,'rating':72,'nat':'Cyprus'},
    {'name':'APOEL Youth','pos':'SUB','age':19,'rating':65,'nat':'Cyprus'}
]

# ---------------------------
# TEAM_ROSTERS dictionary (all teams)
# ---------------------------

TEAM_ROSTERS = {
    # Champions League
    'real_madrid': REAL_MADRID_PLAYERS,
    'barcelona': BARCELONA_PLAYERS,
    'atletico_madrid': ATLETICO_MADRID_PLAYERS,
    'sevilla': SEVILLA_PLAYERS,
    'bayern_munich': BAYERN_MUNICH_PLAYERS,
    'borussia_dortmund': BORUSSIA_DORTMUND_PLAYERS,
    'rb_leipzig': RB_LEIPZIG_PLAYERS,
    'bayer_leverkusen': BAYER_LEVERKUSEN_PLAYERS,
    'inter_milan': INTER_MILAN_PLAYERS,
    'ac_milan': AC_MILAN_PLAYERS,
    'juventus': JUVENTUS_PLAYERS,
    'napoli': NAPOLI_PLAYERS,
    'paris_saint_germain': PARIS_SAINT_GERMAIN_PLAYERS,
    'marseille': MARSEILLE_PLAYERS,
    'monaco': MONACO_PLAYERS,
    'lyon': LYON_PLAYERS,
    'benfica': BENFICA_PLAYERS,
    'porto': PORTO_PLAYERS,
    'sporting_cp': SPORTING_CP_PLAYERS,
    'ajax': AJAX_PLAYERS,
    'psv_eindhoven': PSV_EINDHOVEN_PLAYERS,
    'feyenoord': FEYENOORD_PLAYERS,
    'club_brugge': CLUB_BRUGGE_PLAYERS,
    'anderlecht': ANDERLECHT_PLAYERS,
    'galatasaray': GALATASARAY_PLAYERS,
    'fenerbahce': FENERBAHCE_PLAYERS,
    'celtic': CELTIC_PLAYERS,
    'rangers': RANGERS_PLAYERS,
    'rb_salzburg': RB_SALZBURG_PLAYERS,
    'shakhtar_donetsk': SHAKHTAR_DONETSK_PLAYERS,
    'young_boys': YOUNG_BOYS_PLAYERS,
    'red_star_belgrade': RED_STAR_BELGRADE_PLAYERS,

    # Europa League
    'real_sociedad': REAL_SOCIEDAD_PLAYERS,
    'villarreal': VILLARREAL_PLAYERS,
    'real_betis': REAL_BETIS_PLAYERS,
    'athletic_bilbao': ATHLETIC_BILBAO_PLAYERS,
    'eintracht_frankfurt': EINTRACHT_FRANKFURT_PLAYERS,
    'union_berlin': UNION_BERLIN_PLAYERS,
    'freiburg': SC_FREIBURG_PLAYERS,
    'hoffenheim': TSG_HOFFENHEIM_PLAYERS,
    'as_roma': AS_ROMA_PLAYERS,
    'lazio': LAZIO_PLAYERS,
    'atalanta': ATALANTA_PLAYERS,
    'fiorentina': FIORENTINA_PLAYERS,
    'lille': LILLE_PLAYERS,
    'nice': NICE_PLAYERS,
    'rennes': RENNES_PLAYERS,
    'lens': LENS_PLAYERS,
    'braga': BRAGA_PLAYERS,
    'vitoria_guimaraes': VITORIA_GUIMARAES_PLAYERS,
    'rio_ave': RIO_AVE_PLAYERS,
    'az_alkmaar': AZ_ALKMAAR_PLAYERS,
    'fc_twente': FC_TWENTE_PLAYERS,
    'fc_utrecht': FC_UTRECHT_PLAYERS,
    'genk': GENK_PLAYERS,
    'royal_antwerp': ROYAL_ANTWERP_PLAYERS,
    'olympiacos': OLYMPIACOS_PLAYERS,
    'panathinaikos': PANATHINAIKOS_PLAYERS,
    'slavia_prague': SLAVIA_PRAGUE_PLAYERS,
    'dynamo_kyiv': DYNAMO_KYIV_PLAYERS,
    'copenhagen': COPENHAGEN_PLAYERS,
    'bodo_glimt': BODO_GLIMT_PLAYERS,
    'maccabi_haifa': MACCABI_HAIFA_PLAYERS,
    'apoel': APOEL_PLAYERS
}

# End of file
