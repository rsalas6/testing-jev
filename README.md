# testing-jev

Playing with Jev, TypeSafe AI's first System One model.

## Run

With [Task](https://taskfile.dev) (builds the image automatically):

```sh
task                              # list tasks
task run:test-1-types.py
task run -- test-1-types.py --raw          # full API response
task run:test-2-parallel.py
task run -- test-2-parallel.py --answers   # what it decided
task run:test-3-calibration.py
task repl                         # Python REPL in the container
task shell                        # bash in the container
task clean                        # drop the image
```

Save an output when you want to keep it: `task run:test-1-types.py > test-1.txt`.

Plain Docker works too:

```sh
docker build -t jev-test .
docker run --rm -it --env-file .env -v "$PWD:/app" jev-test python test-1-types.py
```

`.env` holds `TYPESAFE_API_KEY` (see `.env.example`) and is passed in at run time with `--env-file`. It is
never baked into the image (`.dockerignore` keeps it out of the build context).

## Files

| File | What it does |
| --- | --- |
| `test-1-types.py` | The three question types: Choice, Score, Noul |
| `test-2-parallel.py` | 1 question vs. 20 in one call: latency and cost |
| `test-3-calibration.py` | Does "0.8" really happen 80% of the time? |

Every script takes `--save`, which writes its output next to it as `<script>-output.txt`.

## Notes

- Endpoint: `POST https://api.typesafe.ai/v1/systemone`, `Authorization: Bearer <key>`.
- Over raw HTTP, `model` is required (`jev-latest`); the SDK fills it in.
- `confidence` is derived from the probabilities: `(n * peak - 1) / (n - 1)`.
