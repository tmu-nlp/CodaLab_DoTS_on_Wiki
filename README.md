# DoTS/Wiki: Automatic Program and Document for CodaLab Bundle

We added the following corpora repos via:
- SWiPE: ``git submodule add https://github.com/salesforce/simplification.git Corpora/SWiPE``
- Klexikon: ``git submodule add https://github.com/dennlinger/klexikon.git Corpora/Klexikon``
- JADOS: ``git submodule add https://github.com/tmu-nlp/JADOS.git Corpora/JADOS-Wiki``

## Usage:
So you need to clone to the local via:

    git clone --recurse-submodules https://github.com/tmu-nlp/CodaLab_DoTS_on_Wiki.git
    cd CodaLab_DoTS_on_Wiki

Requirements:

    pip install -r requirements.txt    # for Python
    Rscript requirements.R             # for R

Setup Docker for CodaLab workers:

    docker buildx build -t zchen0420/sari:0 . --push
    # refer to the same image name in competition.yaml

Build:

    cd Bundle
    ./create.sh

- Upload the generated ``bundle.zip`` to [CodaLab](https://codalab.lisn.upsaclay.fr/competitions/s3_create_competition).
- Check or delete the ``tmp`` folder for your confirmation.

## How it works?

### Scoring Program:
- CodaLab workers accept a submission and unzip it into a temporary directory ``$input`` as ``res`` folder (along with ``ref`` as the reference to execute ``score.py``, as defined in ``metadata``).
- ``score.py`` (requiring the above docker image) writes the scores to ``$output/scores.txt``, which are projected on to the leaderboard defined in ``competition.yaml``.

If you want to modify the scores, check both ``score.py`` and ``competition.yaml``.

### Interface:
- You need to configure the ``competition.yaml`` (e.g., ``start_date`` and ``end_date``) and modify the corresponding html files in ``Bundle/html``.
- Note that images (i.e., svg files) have been uploaded to a separate server, accessible by ``<a href="https://cl.sd.tmu.ac.jp/~zchen/...">``.