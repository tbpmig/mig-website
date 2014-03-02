from django import template

register = template.Library()

@register.filter
def partition(thelist,n):
    try:
        n=int(n)
        thelist = list(thelist)
    except (ValueError, TypeError):
        return [thelist]
    p=len(thelist)/n
    return[thelist[p*i:p*(i+1)] for i in range (n-1)]+[thelist[p*(i+1):]]
