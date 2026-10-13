#!/bin/bash
# Runs all of Westminster's in-game tests (CK3 closed, Steam running): spikes b, d, e, f, g and h in one run (b
# needs 40 days of game time, so the game is unpaused), spike c on its own (it re-elects every seat), then the
# gameplay suites: riots and the Crown, the Commons, elections, coalitions, campaigns, careers, parties, politics,
# leadership, the majority, ideology and intrigue (tools/ck3_test/gen_*.py).
# Spike a (the map) passes when the game loads at all. Needs tools/ck3_test/saves/wm_2025.ck3 (make_save.sh).
set -u
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT"
export HARNESS=westminster/tools/ck3_test/harness MODS="mod/westminster.mod" SAVE=westminster/tools/ck3_test/saves/wm_2025.ck3
mkdir -p westminster/tools/test_out
fail=0
for suite in bdefgh c; do
	python3 westminster/tools/ck3_test/gen_spikes.py "$suite" >/dev/null
	UNPAUSE=$([ "$suite" = c ] || echo 1) WAIT_LOOPS=80 common/ck3_test/run_test.sh "westminster/tools/test_out/spikes_$suite.log" >/dev/null 2>&1
	python3 common/ck3_test/report.py "westminster/tools/test_out/spikes_$suite.log" | grep -v "  ->"
	python3 common/ck3_test/report.py "westminster/tools/test_out/spikes_$suite.log" | grep -q "FAIL\|did not reach" && fail=1
done
# Gameplay suites: riots and the Crown, the Commons, elections (the timed ones need the clock running)
for g in gameplay:1 commons: elections:1 coalitions: campaign: career: parties: politics: leadership: majority: ideology: intrigue:; do
	name=${g%%:*}; timed=${g#*:}
	python3 "westminster/tools/ck3_test/gen_$name.py" >/dev/null
	UNPAUSE=$timed WAIT_LOOPS=120 common/ck3_test/run_test.sh "westminster/tools/test_out/$name.log" >/dev/null 2>&1
	python3 common/ck3_test/report.py "westminster/tools/test_out/$name.log" | grep -v "  ->"
	python3 common/ck3_test/report.py "westminster/tools/test_out/$name.log" | grep -q "FAIL\|did not reach" && fail=1
done
python3 common/tools/ck3_checks.py errorlog wm_ || fail=1
exit $fail
