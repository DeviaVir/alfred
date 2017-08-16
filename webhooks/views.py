import socket
from django.http import HttpResponse
from alfred.settings import SW_REGION, SW_TOKEN, WEBHOOK_SECRET


def index(request):
    resp = 'NOK'

    if request.GET.get('secret') != WEBHOOK_SECRET:
        return HttpResponse(resp)

    ip = request.GET.get('ip')
    if request.method == 'POST':
        if request.POST.get('current_state') == 'DOWN':
            hostname = request.POST.get('check_params', {}).get('hostname')
            if hostname:
                ip = socket.gethostbyname(hostname)

    if ip:
        from scaleway.apis import ComputeAPI
        api = ComputeAPI(region=SW_REGION, auth_token=SW_TOKEN)
        servers = api.query().servers.get().get('servers', [])

        actionable_host = {}
        for server in servers:
            if server.get('public_ip', {}).get('address', '') == ip:
                actionable_host = server
                break

        if actionable_host:
            api.query().servers(actionable_host.get('id')).action.post(
                {'action': 'reboot'})
            resp = 'OK'

    return HttpResponse(resp)
