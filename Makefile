.PHONY: build-e4b build-12b split base dev heldout review

build-e4b:
	python scripts/build.py --model e4b

build-12b:
	python scripts/build.py --model 12b

split:
	python scripts/make_splits.py

base:
	python scripts/score.py --split dev --tag p00-base

dev:
	python scripts/score.py --split dev --tag $(TAG)

heldout:
	python scripts/score.py --split heldout --tag $(TAG)

review:
	python scripts/review.py $(TAG) $(ID)
