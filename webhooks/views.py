import socket
import logging
import json
from django.http import HttpResponse
from alfred.settings import SW_REGION, SW_TOKEN, WEBHOOK_SECRET
from django.views.decorators.csrf import csrf_exempt


# Get an instance of a logger
logger = logging.getLogger(__name__)


@csrf_exempt
def index(request):
    resp = 'NOK'

    if request.GET.get('secret') != WEBHOOK_SECRET:
        return HttpResponse(resp)

    ip = request.GET.get('ip')
    if request.method == 'POST':
        data = json.loads(request.body)
        logger.error(data)
        if data.get('current_state') == 'DOWN' and \
                'test' not in data.get('description', ''):
            hostname = data.get('check_params', {}).get('hostname')
            if hostname:
                ip = socket.gethostbyname(hostname)

    if ip:
        from scaleway.apis import ComputeAPI
        api = ComputeAPI(region=SW_REGION, auth_token=SW_TOKEN)
        servers = api.query().servers.get().get('servers', [])

        actionable_host = {}
        for server in servers:
            logger.error(server)
            if server.get('public_ip', {}).get('address', '') == ip:
                if server.get('state') == 'running' and \
                        server.get('state_detail') == 'booted':
                    logger.error('passed')
                    actionable_host = server
                break

        if actionable_host:
            api.query().servers(actionable_host.get('id', '')).action.post(
                {'action': 'reboot'})
            resp = 'OK'

    if resp == 'NOK':
        logger.error('NOK')
    else:
        logger.error('OK')
    return HttpResponse(resp)
