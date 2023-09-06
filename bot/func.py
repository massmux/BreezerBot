
def add_to_notifications(data_id):
    notifications = get_obj_redis("notificationsxxxxx")
    if notifications == False:
        notifications = []
    if data_id not in notifications:
        notifications.append(data_id)
    if set_obj_redis('notificationsxxxxx', notifications):
        return True
    else:
        return False



def rm_from_notifications(data_id):
    notifications = get_obj_redis("notificationsxxxxx")
    notifications.remove(data_id)
    if set_obj_redis('notificationsxxxxx', notifications):
        return True
    else:
        return False
