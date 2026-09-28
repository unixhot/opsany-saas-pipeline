from datetime import timedelta

import arrow
import mongoengine as db


class BasicDocument(db.Document):
    updated_at = db.DateTimeField(default=lambda: arrow.now().format("YYYY-MM-DD HH:mm:ss"))
    created_at = db.DateTimeField(default=lambda: arrow.now().format("YYYY-MM-DD HH:mm:ss"))

    meta = {
        'abstract': True,
        'queryset_class': db.QuerySet,
        'indexes': [
            '-updated_at',
            '-created_at'
        ]
    }

    def __str__(self):
        return '<{} {}>'.format(self.__class__.__name__, self.pk)

    def __repr__(self):
        return '<{} {}>'.format(self.__class__.__name__, self.pk)

    @classmethod
    def create(cls, **kwargs):
        obj = cls(**kwargs)
        return obj.save()

    def update(self, **kwargs):
        kwargs['updated_at'] = arrow.now().datetime
        for k, v in kwargs.items():
            setattr(self, k, v)
        return self.save()

    @classmethod
    def fetch_all(cls, **kwargs):
        return cls.objects.filter(**kwargs)

    @classmethod
    def counter(cls, **kwargs):
        query_set = cls.fetch_all(**kwargs)
        return query_set.count()

    @classmethod
    def pagination(cls, page=1, per_page=10, order_by='-created_at', **kwargs):
        query_set = cls.fetch_all(**kwargs)
        total = query_set.count()
        query_set = query_set.order_by(order_by)

        current_page = query_set[(page - 1) * per_page: page * per_page]
        return current_page, total

    @classmethod
    def fetch_one(cls, **kwargs):
        return cls.objects.filter(**kwargs).first()

    @classmethod
    def find_by_pk(cls, pk):
        return cls.objects.get(pk=pk)

    @classmethod
    def find_by_pks(cls, pks):
        return cls.objects.filter(pk__in=pks)

    @classmethod
    def existed_record(cls, record=None, **kwargs):
        if not kwargs:
            return False
        for key, value in kwargs.items():
            counter = cls.counter(**{key: value})
            if counter > 1:
                return True
            if counter == 1:
                if record is None or not isinstance(record, cls):
                    return True
                log_record = cls.fetch_one(**{key: value})
                if log_record.pk != record.pk:
                    return True
        return False

    @classmethod
    def check_field_unique(cls, code: int, field_name: str, field_value):
        """
        0: 不唯一
        1：唯一
        """
        id_query = cls.fetch_one(code=code)
        name_query = cls.fetch_one(**{field_name: field_value})
        if name_query:
            if id_query != name_query:
                return False
        return True

    def to_dict(self):
        dt = {}
        dt["updated_at"] = self.updated_at
        dt["created_at"] = self.created_at
        return dt

    def get_date_time(self, date_time):
        if date_time:
            return (date_time + timedelta(hours=8)).strftime("%Y-%m-%d %H:%M:%S")
        else:
            return date_time
        # return str(self.start_timestamp).split(".")[0]

