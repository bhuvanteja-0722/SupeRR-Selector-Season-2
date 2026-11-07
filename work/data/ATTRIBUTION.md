# Cricsheet source data and attribution

Public Cricsheet Ashwin CSV archives and player identity registers downloaded 7 November 2026 are included under this directory. Cricsheet licenses most of its data under the Open Data Commons Attribution License (ODC-BY). Check the [Cricsheet licensing page](https://cricsheet.org/licensing/) and the full license before reuse. Preserve the source notices and attribute Cricsheet and the archive/register data in any redistribution or derived publication. No Cricsheet endorsement is implied.

Downloads are from [Cricsheet downloads](https://cricsheet.org/downloads/) and [Cricsheet registers](https://cricsheet.org/register/). The exact URLs, match counts, date spans, usage and file sizes are listed in `outputs/dataset_inventory.csv`.

The model's domestic/franchise feature inputs are 18 T20 archives. `ipl_csv2.zip` provides historical outcome labels. Men's T20I, extended IT20 and ICC Men's T20 World Cup files are included as research/identity references and are not used as domestic model feature inputs. `people.csv` and `names.csv` assist cross-competition identity resolution. The model does not use any proprietary Rajasthan Royals data; the challenge pack is not available yet.
