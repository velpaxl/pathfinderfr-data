#!/usr/bin/python3
# -*- coding: utf-8 -*-

import urllib.request
import yaml
import sys
import html
import re
from bs4 import BeautifulSoup
from lxml import html


## Configurations pour le lancement
MOCK_RACE = None
#MOCK_RACE = "mocks/race-demielfe.html"       # décommenter pour tester avec une classe pré-téléchargée


#
# cette fonction extrait le texte du prochain élément après ...
#
def findAfter(html, afterTag, afterCond, searched):
    elements = html.find_next(afterTag, afterCond).next_siblings
    for el in elements:
        if el.name == searched:
            return el.text.strip()

#
# cette fonction extrait le texte pour une propriété <b>propriété</b> en prenant le texte qui suit
#
def findProperty(html, propName):
    for el in html:
        if el.name == 'b' and el.text.lower().startswith(propName.lower()):
            value = ""
            for e in el.next_siblings:
                if e.name == 'br':
                    break
                elif e.string:
                    value += e.string
                else:
                    value += e
            return value.replace('.','').strip()
    return None

#
# cette fonction permet de sauter à l'élément recherché et retourne les prochains éléments
#
def jumpTo(html, afterTag, afterCond, elementText):
    seps = content.find_all(afterTag, afterCond);
    for s in seps:
        if s.text.lower().strip().startswith(elementText.lower()):
            return s.next_siblings

races = []
with open("../data/races.yml", 'r') as stream:
    try:
        races = yaml.safe_load(stream)
    except yaml.YAMLError as exc:
        print(exc)
        exit(1)


liste = []


# itération sur chaque page
for data in races:
    
    #if not data['Nom'] == "Wayang":
    #    continue
    
    found = False
    link = data[u'Référence']

    print("Processing %s" % link)
    pageURL = link

    if MOCK_RACE:
        content = BeautifulSoup(open(MOCK_RACE),features="lxml").body
    else:
        content = BeautifulSoup(urllib.request.urlopen(pageURL).read(),features="lxml").body

    # traits alternatifs
    section = jumpTo(html, 'h2',{'class':'separator'}, u"Traits raciaux alternatifs")
    for s in section:
        if s.name == 'h2':
            if not found:
                print("Aucun trait racial alternatif trouvé!")

            break; # avoid jumping to other sections
        if s.name == 'div' and 'class' in s.attrs and "row" in s.attrs['class']:
            for attr in s.find_all('li'):
                descr = ""
                remplaceText = ""
                modifieText = ""
                for el in attr.children:
                    if el.name == 'b':
                        name = el.text.strip()
                        if name.endswith('.'):
                            name = name[:-1]
                    
                    # ugly hacks for aasimar
                    elif el.name == 'i' and el.string and el.string.startswith("Ce trait racial remplace la langue céleste et altère le sous-type natif."):
                        modifieText = "langues et extérieur natif"
                    # ugly hacks for oréade
                    elif el.name == 'i' and el.string and el.string.startswith("Ce trait racial remplace le type, le sous-type et les langues."):
                        remplaceText = "extérieur natif et langues"
                    # ugly hacks for duergar
                    elif el.name == 'i' and el.text.startswith("Ce trait racial remplace le pouvoir magique"):
                        modifieText = "pouvoirs magiques"
                    elif el.name == 'i' and el.text.startswith("Ce trait racial remplace les pouvoirs magiques"):
                        modifieText = "pouvoirs magiques"

                    elif el.name == 'i' and el.string and el.string.startswith("Ce trait remplace "):
                        remplaceText = el.string[18:].strip()
                    elif el.name == 'i' and el.string and el.string.startswith("Ce trait racial remplace "):
                        remplaceText = el.string[25:].strip()
                        
                    elif el.name == 'i' and el.string and el.string.startswith("Ce trait racial modifie "):
                        descr += el.string
                        modifieText = el.string[24:].strip()
                        
                    elif el.string:
                        descr += el.string
                    elif el.name == 'i':
                        descr += el.text
                
                
                # ugly hacks for duergar
                if name == "Traits nains" and data['Nom'] == "Duergar":
                    remplaceText = "stabilité et immunités des duergars"
                # ugly hacks for suli
                elif data['Nom'] == "Suli":
                    modifieText = "assaut élémentaire (Sur)"
                # ugly hacks for duergar
                elif name == u"Étranger des arbres" and data['Nom'] == "Vanara":
                    modifieText = "vitesse normale"
                
                # liste de traits remplacés
                remplace = []
                if remplaceText.endswith('.'):
                    remplaceText = remplaceText[:-1]
                if len(remplaceText) > 0:
                    traits = re.split('et |, ', remplaceText)
                    for altTrait in traits:
                        altTrait = altTrait.strip().lower()
                        
                        # ugly hacks for humain
                        if altTrait == u"le don supplémentaire de niveau 1":
                            altTrait = u"don en bonus"
                        elif altTrait == u"le bonus racial de +2 à une caractéristique":
                            altTrait = u"caractéristiques"
                        elif altTrait == u"le don supplémentaire":
                            altTrait = u"don en bonus"
                            
                                            
                        
                        # vérifier que le trait existe!!
                        exists = False
                        for t in data["Traits"]:
                            #print("Check: '%s' == '%s'" % (t["Nom"].lower(),altTrait))
                            if t["Nom"].lower() in altTrait:
                                remplace.append(t["Nom"])
                                exists = True
                        # non-trouvé!
                        if not exists:
                            print("Trait alternatif '%s' invalide. Aucune correspondance de '%s'" % (name, altTrait))
                            #exit(1)
                
                # liste de traits modifiés
                modifie = []
                if modifieText.endswith('.'):
                    modifieText = modifieText[:-1]
                if len(modifieText) > 0:
                    traits = re.split('et |, ', modifieText)
                    for altTrait in traits:
                        altTrait = altTrait.strip().lower()
                        
                        # vérifier que le trait existe!!
                        exists = False
                        for t in data["Traits"]:
                            #print("Check: '%s' == '%s'" % (t["Nom"].lower(),altTrait))
                            if t["Nom"].lower() in altTrait:
                                modifie.append(t["Nom"])
                                exists = True
                        # non-trouvé!
                        if not exists:
                            print("Trait alternatif '%s' invalide. Aucune correspondance de '%s'" % (name, altTrait))
                            #exit(1)
                
                if len(modifie) == 0 and len(remplace) == 0:
                    print("Trait alternatif '%s' invalide. Aucun trait de remplacement/modifié trouvé!" % name)
                    exit(1)                
                
                racefeature = {}
                racefeature[u'01Nom'] = name
                racefeature[u'02Race'] = data['Nom']
                racefeature[u'03Source'] = "MR"
                racefeature[u'04Description'] = descr.strip()
                if len(remplace) > 0:
                    racefeature[u'05Remplace'] = remplace
                if len(modifie) > 0:
                    racefeature[u'05Modifie'] = modifie
                racefeature[u'06Référence'] = pageURL
                racefeature['EMPTY'] = ""
                found = True
                
                # ajouter race
                liste.append(racefeature)

    if MOCK_RACE:
        break

yml = yaml.safe_dump(liste,default_flow_style=False, allow_unicode=True)
yml = yml.replace(u'01Nom',u'Nom')
yml = yml.replace(u'02Race',u'Race')
yml = yml.replace(u'03Source',u'Source')
yml = yml.replace(u'04Description',u'Description')
yml = yml.replace(u'05Remplace',u'Remplace')
yml = yml.replace(u'05Modifie',u'Modifie')
yml = yml.replace(u'06Référence',u'Référence')
yml = yml.replace("EMPTY: ''",'')
print(yml)
