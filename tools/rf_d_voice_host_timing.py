"""Read render timings from the offline RackForge host probe."""

SAMPLE_RATE = 48_000


def host_timing(logs, block, frames, thread_cpu):
    lines = logs.decode().splitlines()
    rows = [tuple(map(int, line.split(",")[1:])) for line in lines if line.startswith("RF_D_EXT,")]
    assert [row[0] for row in rows] == [2, 3], rows
    cpu_rows = [tuple(map(int, line.split(",")[1:])) for line in lines if line.startswith("RF_D_EXT_CPU,")]
    assert [row[0] for row in cpu_rows] == ([2, 3] if thread_cpu else []), cpu_rows
    cpu = {channel: (maximum, misses) for channel, maximum, misses in cpu_rows}
    results = []
    for channel, count, maximum, misses, faults in rows:
        assert count == (frames + block - 1) // block and faults == 0, (block, rows)
        result = dict(capture_input=channel, blocks=count, max_ns=maximum, deadline_misses=misses)
        if thread_cpu:
            assert cpu[channel][0] > 0, cpu_rows
            result["cpu_max_ns"], result["cpu_deadline_misses"] = cpu[channel]
        results.append(result)
    return results


def require_realtime(results, block, thread_cpu):
    prefix = "cpu_" if thread_cpu else ""
    for result in results:
        assert result[prefix + "deadline_misses"] == 0, result
        if block == 128:
            assert result[prefix + "max_ns"] < block * 1e9 / (2 * SAMPLE_RATE), result
