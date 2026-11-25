"""Discovery helpers for single-page applications (SPA)."""
import re

from core.config import BAD_TYPES

# Route definitions used by popular SPA frameworks, e.g.
# { path: '/users' }, <Route path="/users">, <Link to="/users">
ROUTE_DEF_RE = re.compile(
    r'(?:\bpath|\bto|\broute)\s*[:=]\s*[\'"`{]+\s*(/[\w\-./:]{1,120})[\'"`}]',
    re.IGNORECASE)

# Programmatic navigation, e.g. router.push('/users'), navigate('/users')
ROUTE_NAV_RE = re.compile(
    r'(?:router\.(?:push|replace)|\$router\.(?:push|replace)|navigate|'
    r'history\.push)\s*\(\s*[\'"`](/[\w\-./:]{1,120})[\'"`]',
    re.IGNORECASE)

# Quoted hash routes, e.g. '#/users', '#!/users'
HASH_ROUTE_TEXT_RE = re.compile(r'[\'"]#!?(/(?:[\w\-]+[./]?)+)[\'"]')

# Hash route inside a single link/URL
HASH_ROUTE_RE = re.compile(r'#!?(/(?:[\w\-]+[./]?)+)')

FORM_RE = re.compile(r'(?is)<form\b([^>]*)>(.*?)</form>')
FORM_FIELD_RE = re.compile(r'(?is)<(?:input|select|textarea)\b[^>]*>')
SKIP_FIELD_TYPES = ('submit', 'button', 'reset', 'image', 'file')


def clean_route(route):
    """Validate and normalize a discovered client-side route path."""
    if not route:
        return None
    route = route.split('?')[0].split('#')[0].rstrip('/')
    if not route or route == '/' or route.startswith('//'):
        return None
    if '..' in route or route.endswith(BAD_TYPES):
        return None
    return route


def hash_route_of(link):
    """Return the route path of a hash-based link such as '#/users'."""
    match = HASH_ROUTE_RE.search(link)
    if match:
        return clean_route(match.group(1))
    return None


def extract_hash_routes(text):
    """Extract hash-based routes ('#/x', '#!/x') from a response body."""
    routes = set()
    for match in HASH_ROUTE_TEXT_RE.findall(text):
        route = clean_route(match)
        if route:
            routes.add(route)
    return routes


def extract_spa_routes(text):
    """Extract client-side route paths from JS frameworks' route tables."""
    routes = set()
    for regex in (ROUTE_DEF_RE, ROUTE_NAV_RE):
        for match in regex.findall(text):
            route = clean_route(match)
            if route:
                routes.add(route)
    return routes


def _attr(text, name):
    match = re.search(name + r'\s*=\s*[\'"]([^\'"]*)[\'"]', text,
                      re.IGNORECASE)
    if match is None:
        match = re.search(name + r'\s*=\s*([^\s>]+)', text, re.IGNORECASE)
    return match.group(1) if match else None


def extract_forms(response):
    """Extract form actions, methods and parameter names from HTML."""
    forms = []
    for attrs, body in FORM_RE.findall(response):
        action = _attr(attrs, 'action') or ''
        method = (_attr(attrs, 'method') or 'get').lower()
        params = []
        for field in FORM_FIELD_RE.findall(body):
            field_type = (_attr(field, 'type') or '').lower()
            if field_type in SKIP_FIELD_TYPES:
                continue
            name = _attr(field, 'name')
            if name and name not in params:
                params.append(name)
        forms.append({'action': action, 'method': method, 'params': params})
    return forms


def absolutize(link, base_url, main_url):
    """Resolve a (possibly relative) URL against the page it was found on."""
    if not link:
        return base_url
    if link.startswith('http://') or link.startswith('https://'):
        return link
    if link.startswith('//'):
        return main_url.split('//')[0] + link
    if link.startswith('/'):
        return main_url + link
    if base_url.count('/') > 2:
        base = base_url.rsplit('/', 1)[0]
    else:
        base = base_url
    return base + '/' + link
