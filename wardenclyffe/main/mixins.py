import csv

from django.http.response import HttpResponse


class CSVResponseMixin():

    def render_csv_response(self, filename, headers, rows):
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = \
            'attachment; filename=' + filename + '.csv'
        writer = csv.writer(response)

        writer.writerow(headers)

        for row in rows:
            try:
                writer.writerow(row)
            except csv.Error:
                pass

        return response
