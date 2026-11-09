# SolarEdge Basic Monitoring voor Home Assistant

Een custom Home Assistant-integratie voor SolarEdge Monitoring API v2. De integratie gebruikt OAuth 2.0 met de Client ID en Client Secret van een SolarEdge Developer-app en maakt sensoren aan voor de scalaire waarden uit de site-, device- en measurement-responses. Bij tijdreeksen wordt de laatste rij als actuele sensorwaarde gebruikt.

## SolarEdge-app voorbereiden

1. Maak of open een app in het [SolarEdge Developer-portaal](https://developer.solaredge.com/).
2. Geef de app de scopes/rechten voor Basic Monitoring en autoriseer de gewenste site.
3. Voeg als OAuth redirect-URL toe: `https://my.home-assistant.io/redirect/oauth`.
4. Noteer de OAuth Client ID en Client Secret. Deel deze gegevens niet; de integratie slaat ze op in de Home Assistant-configuratie.

## Installatie via HACS

1. Open **HACS → Integraties → ⋮ → Aangepaste repositories**.
2. Voeg `https://github.com/bart1604/solaredge_v2` toe als repository van het type **Integration**.
3. Download **SolarEdge Basic Monitoring** en herstart Home Assistant.
4. Ga naar **Instellingen → Apparaten en diensten → Integratie toevoegen** en kies **SolarEdge Basic Monitoring**.
5. Vul het site-ID, de Client ID en de Client Secret in en rond de SolarEdge-toestemming in de browser af.

De OAuth-toegangstokens worden automatisch vernieuwd met de refresh-token wanneer SolarEdge die levert. API-responses worden opgehaald via de SolarEdge API v2 site-, overview-, devices-, measurements-, energy- en power-resources. Polling vindt eenmaal per uur plaats; resources die niet beschikbaar zijn voor de gekozen site of OAuth-scopes verhinderen niet dat andere responses worden verwerkt.

## Ontwikkeling

Integratiecode staat in `custom_components/solaredge_api_v2/`. Er zijn geen externe Python-pakketten nodig buiten Home Assistant.
