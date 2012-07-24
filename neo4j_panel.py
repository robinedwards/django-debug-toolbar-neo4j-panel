import os
import time
import operator
from django.utils.html import escape
from django.dispatch import Signal
from django.utils.safestring import mark_safe
from django.template import Template, Context
from debug_toolbar.panels import DebugPanel
from django.utils.translation import ugettext_lazy as _, ungettext
from debug_toolbar.utils import get_stack, tidy_stacktrace
import neo4jrestclient.request
import logging
logger = logging.getLogger(__name__)

__all__ = ['Neo4jPanel']

neo4j_call = Signal(providing_args=['duration', 'calls'])

OldRequest = neo4jrestclient.request.Request


def render_headers(headers):
    header_s = u""

    if headers:
        for k, v in headers.iteritems():
            header_s += u"%s: %s\n" % (k, v)
    else:
        header_s = u"None"

    return header_s


class TrackingRequest(OldRequest):

    def __init__(self, *args, **kwargs):
        super(TrackingRequest, self).__init__(*args, **kwargs)

    def _make_call_dict(self, depth, method, url, data, headers):
        trace = tidy_stacktrace(reversed(get_stack()))[1:-depth] or []
        data_s = u""

        if data:
            for k, v in data.iteritems():
                data_s += u"%s: %s\n" % (k, v)
        else:
            data_s = u"None"

        return {'method': method, 'url': url, 'trace': trace,
                'data': data_s, 'headers': render_headers(headers)}

    def _request(self, method, url, data={}, headers={}):
        call = self._make_call_dict(2, method, url, data, headers)

        try:
            start = time.time()
            response, content = super(TrackingRequest, self)._request(method, url, data, headers)
            call['response'] = render_headers(response) + u"\n\n" + unicode(content)
        finally:
            stop = time.time()
            duration = (stop - start) * 1000

            neo4j_call.send_robust(sender=self, duration=duration, calls=(call,))

        return response, content

neo4jrestclient.request.Request = TrackingRequest


class Neo4jPanel(DebugPanel):
    name = 'Neo4j'
    has_content = True

    def __init__(self, *args, **kwargs):
        super(Neo4jPanel, self).__init__(*args, **kwargs)
        self.calls = []
        neo4j_call.connect(self._add_call)

    def _add_call(self, sender, duration, calls, **kw):
        for call in calls:
            call['trace'] = render_stacktrace(call['trace'])
        self.calls.append({'duration': duration, 'calls': calls})

    def nav_title(self):
        return _("Neo4j")
    title = nav_title

    def nav_subtitle(self):
        calls = len(self.calls)
        duration = sum(map(operator.itemgetter('duration'), self.calls))

        logger.debug('%d requests in %.2fms' % (calls, duration))
        return ungettext('%(calls)d call in %(duration).2fms',
                         '%(calls)d calls in %(duration).2fms',
                         calls) % {'calls': calls, 'duration': duration}

    def url(self):
        return ''

    def content(self):
        context = {'calls': self.calls, 'commands': {}}
        for tr in self.calls:
            for call in tr['calls']:
                context['commands'][call['method']] = \
                        context['commands'].get(call['method'], 0) + 1
        return Template(template).render(Context(context))


def render_stacktrace(trace):
    stacktrace = []
    for frame in trace:
        params = map(escape, frame[0].rsplit(os.path.sep, 1) + list(frame[1:]))
        try:
            stacktrace.append(u'<span class="path">{0}/</span><span class="file">{1}</span> in <span class="func">{3}</span>(<span class="lineno">{2}</span>)\n <span class="code">{4}</span>'.format(*params))
        except IndexError:
            # This frame doesn't have the expected format, so skip it and move on to the next one
            continue
    return mark_safe('\n'.join(stacktrace))

template = """
{% load i18n %}
<h4>{% trans "Calls" %}</h4>
<table>
<thead>
<tr>
<th>{% trans "Method" %}</th>
<th>{% trans "Count" %}</th>
</tr>
</thead>
<tbody>
{% for command, count in commands.iteritems %}
<tr>
<td>{{ command }}</td>
<td>{{ count }}</td>
</tr>
{% endfor %}
</tbody>
</table>

<table>
<thead>
<tr>
<th>{% trans "Duration" %}</th>
<th>{% trans "Method" %}</th>
<th>{% trans "Url" %}</th>
<th>{% trans "Headers" %}</th>
<th>{% trans "Action" %}</th>
</tr>
</thead>

<tbody>
{% for tr in calls %}
{% for call in tr.calls %}
<tr>
<td>{% if forloop.first %}{{ tr.duration|floatformat:2 }} ms{% endif %}</td>
<td>{{ call.method }}</td>
<td>{{ call.url }}</td>
<td>{{ call.headers }}</td>
<td>
{% if call.data != 'None' %}
<a href="#" class="djdtNeo4jShowData">{% trans "Show payload" %}</a>
{% endif %}
<a href="#" class="djdtNeo4jShowTrace">{% trans "Show stacktrace" %}</a>
<a href="#" class="djdtNeo4jShowResponse">{% trans "Show  response" %}</a>
</td>
</tr>

{% if call.trace %}
<tr class="djdtNeo4jTrace">
<td colspan="4">
<pre class="stack">{{ call.trace }}</pre>
</td>
</tr>
{% endif %}

{% if call.response %}
<tr class="djdtNeo4jResponse">
<td colspan="4">
<pre class="stack">{{ call.response|safe }}</pre>
</td>
</tr>
{% endif %}

{% if call.trace %}
<tr class="djdtNeo4jData">
<td colspan="4">
<pre class="stack">{{ call.data }}</pre>
</td>
</tr>
{% endif %}

{% endfor %}
{% endfor %}
</tbody>
</table>
<script type="text/javascript">
$('.djdtNeo4jTrace').attr('style', 'display:none');
$('.djdtNeo4jResponse').attr('style', 'display:none');
$('.djdtNeo4jData').attr('style', 'display:none');
$('.djdtNeo4jShowData').click(function () {
$(this).parent().parent().next().next().next().toggle();
});
$('.djdtNeo4jShowTrace').click(function () {
$(this).parent().parent().next().toggle();
});
$('.djdtNeo4jShowResponse').click(function () {
$(this).parent().parent().next().next().toggle();
});
</script>
"""
