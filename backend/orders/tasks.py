from celery import shared_task

from . import services
from .models import CarePlan


@shared_task(bind=True, max_retries=3)
def generate_care_plan(self, care_plan_id):
    care_plan = CarePlan.objects.select_related('order__patient').get(id=care_plan_id)
    order = care_plan.order
    patient = order.patient

    care_plan.status = 'processing'
    care_plan.save()

    try:
        care_plan.content = services.generate_llm_care_plan(patient, order)
        care_plan.status = 'completed'
        care_plan.save()
        return f"CarePlan #{care_plan_id} completed"

    except Exception as exc:
        if self.request.retries < self.max_retries:
            countdown = 2 ** (self.request.retries + 1)
            care_plan.status = 'pending'
            care_plan.save()
            raise self.retry(exc=exc, countdown=countdown)

        care_plan.status = 'failed'
        care_plan.content = f"Failed after {self.max_retries} retries: {exc}"
        care_plan.save()
        return f"CarePlan #{care_plan_id} failed"
