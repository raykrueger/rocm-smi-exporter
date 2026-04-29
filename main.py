from subprocess import check_output
import json
import time
import logging
from prometheus_client import start_http_server, Gauge, REGISTRY, PROCESS_COLLECTOR, PLATFORM_COLLECTOR

logger = logging.getLogger()
handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s %(name)-12s %(levelname)-8s %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.INFO)

REGISTRY.unregister(PROCESS_COLLECTOR)
REGISTRY.unregister(PLATFORM_COLLECTOR)
# gc_collector has no public variable — unregister by name
REGISTRY.unregister(REGISTRY._names_to_collectors['python_gc_objects_collected_total'])

DEVICE_NAME_FALLBACKS = {
    '0x7551': 'AMD Radeon AI PRO R9700',
}

GENERIC_NAMES = {'N/A', 'AMD Radeon Graphics'}

LABELS = ['device_name', 'device_id', 'subsystem_id']

def resolveDeviceName(card):
    name = card.get('Device Name', 'N/A')
    if name not in GENERIC_NAMES:
        return name
    return DEVICE_NAME_FALLBACKS.get(card.get('Device ID', '').lower(), name)

def floatOrZero(val):
    try:
        return float(val)
    except (TypeError, ValueError):
        return 0.0

gpuEdgeTemperature    = Gauge('rocm_smi_edge_temperature',       'GPU edge temperature (°C)',                    LABELS)
gpuJunctionTemperature = Gauge('rocm_smi_junction_temperature',  'GPU junction/hotspot temperature (°C)',        LABELS)
gpuMemoryTemperature  = Gauge('rocm_smi_memory_temperature',     'GPU memory temperature (°C)',                  LABELS)
gpuSocketPower        = Gauge('rocm_smi_socket_power',           'GPU socket power (W)',                        LABELS)
gpuPowerCap           = Gauge('rocm_smi_power_cap',              'GPU max power cap (W)',                       LABELS)
gpuUsage              = Gauge('rocm_smi_gpu_usage',              'GPU usage (%)',                               LABELS)
gpuVRAMUsage          = Gauge('rocm_smi_gpu_vram_allocation',    'GPU VRAM allocation (%)',                     LABELS)
gpuMemBandwidth       = Gauge('rocm_smi_memory_activity',        'GPU memory read/write bus activity (%)',      LABELS)
gpuFanRPM             = Gauge('rocm_smi_fan_rpm',                'GPU fan speed (RPM)',                        LABELS)
gpuFanSpeed           = Gauge('rocm_smi_fan_speed',              'GPU fan speed (%)',                          LABELS)
gpuGfxClock           = Gauge('rocm_smi_gfx_clock',             'GPU shader clock (MHz)',                      LABELS)
gpuMemClock           = Gauge('rocm_smi_memory_clock',           'GPU memory clock (MHz)',                      LABELS)
gpuThrottleStatus     = Gauge('rocm_smi_throttle_status',        'GPU throttle status (0=normal, non-zero=throttled)', LABELS)
gpuVRAMUsedBytes      = Gauge('rocm_smi_vram_used_bytes',         'GPU VRAM used (bytes)',                           LABELS)
gpuVRAMTotalBytes     = Gauge('rocm_smi_vram_total_bytes',        'GPU VRAM total (bytes)',                          LABELS)


def getGPUMetrics():
    metrics = json.loads(check_output(["rocm-smi", "-a", "--json"]))
    vram = json.loads(check_output(["rocm-smi", "--showmeminfo", "vram", "--json"]))
    for card in vram:
        if card != "system" and card in metrics:
            metrics[card].update(vram[card])
    logger.info("[X] Retrieved metrics from rocm-smi.")
    return metrics


if __name__ == '__main__':
    start_http_server(9393)
    logger.info("[X] Started http server on port 9393..")

    while True:
        metrics = getGPUMetrics()
        for card in metrics:
            if card == "system":
                continue
            c = metrics[card]
            device_name = resolveDeviceName(c)
            labels = {
                'device_name': device_name,
                'device_id': c['Device ID'],
                'subsystem_id': c['Subsystem ID'],
            }

            gpuEdgeTemperature.labels(**labels).set(floatOrZero(c.get('Temperature (Sensor edge) (C)')))
            gpuJunctionTemperature.labels(**labels).set(floatOrZero(c.get('Temperature (Sensor junction) (C)')))
            gpuMemoryTemperature.labels(**labels).set(floatOrZero(c.get('Temperature (Sensor memory) (C)')))

            power = next((c[k] for k in [
                'Current Socket Graphics Package Power (W)',
                'Average Graphics Package Power (W)',
                'average_socket_power (W)',
            ] if k in c and c[k] != 'N/A'), 0)
            gpuSocketPower.labels(**labels).set(floatOrZero(power))
            gpuPowerCap.labels(**labels).set(floatOrZero(c.get('Max Graphics Package Power (W)')))

            gpuUsage.labels(**labels).set(floatOrZero(c.get('GPU use (%)')))
            gpuVRAMUsage.labels(**labels).set(floatOrZero(c.get('GPU Memory Allocated (VRAM%)')))
            gpuMemBandwidth.labels(**labels).set(floatOrZero(c.get('GPU Memory Read/Write Activity (%)')))

            gpuFanRPM.labels(**labels).set(floatOrZero(c.get('Fan RPM')))
            gpuFanSpeed.labels(**labels).set(floatOrZero(c.get('Fan speed (%)')))

            gpuGfxClock.labels(**labels).set(floatOrZero(c.get('current_gfxclk (MHz)')))
            gpuMemClock.labels(**labels).set(floatOrZero(c.get('current_uclk (MHz)')))

            gpuThrottleStatus.labels(**labels).set(floatOrZero(c.get('throttle_status', 0)))
            gpuVRAMUsedBytes.labels(**labels).set(floatOrZero(c.get('VRAM Total Used Memory (B)')))
            gpuVRAMTotalBytes.labels(**labels).set(floatOrZero(c.get('VRAM Total Memory (B)')))

        logger.info("[X] Refreshed GPU metrics.")
        time.sleep(10)
