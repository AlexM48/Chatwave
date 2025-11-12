from django.shortcuts import render, redirect, get_object_or_404
from .models import ChatRoom, Message
from django.http import HttpResponse, JsonResponse
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
from mychat.models import ChatRoom, Message, UserProfile
import logging
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.core.exceptions import ValidationError

logger = logging.getLogger('mychat')


def chat_index(request):
    """Редирект на список комнат"""
    return redirect("mychat:room_list")



@login_required
def send_message(request, room_id):
    if request.method != "POST":
        return JsonResponse({"success": False, "error": "Only POST allowed"})

    room = get_object_or_404(ChatRoom, id=room_id)
    content = request.POST.get("content", "").strip()
    uploaded_file = request.FILES.get("media")
    video_file = None
    image_file = None

    if uploaded_file:
        if uploaded_file.content_type.startswith("video/"):
            video_file = uploaded_file
        elif uploaded_file.content_type.startswith("image/"):
            image_file = uploaded_file
        else:
            return JsonResponse({"success": False, "error": "Unsupported file type"})

    if not content and not uploaded_file:
        return JsonResponse({"success": False, "error": "Empty message"})

    msg = Message(
        room=room,
        user=request.user,
        content=content,
        video=video_file,
        image=image_file
    )

    try:
        msg.full_clean()
        msg.save()
    except ValidationError as e:
        error_message = e.message_dict if hasattr(e, 'message_dict') else str(e)
        return JsonResponse({"success": False, "error": error_message}, status=400)

    logger.info(f"User {request.user.username} отправил сообщение id={msg.id} в room={room.id}")

    # Отправка через WebSocket всем участникам комнаты
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        f"chat_{room_id}",
        {
            "type": "chat_message",
            "action": "message",
            "message_id": msg.id,
            "username": request.user.username,
            "is_superuser": request.user.is_superuser,
            "content": msg.content,
            "video_url": msg.video.url if msg.video else None,
            "image_url": msg.image.url if msg.image else None,
        }
    )

    # Возвращаем JSON с URL медиа
    return JsonResponse({
    "success": True,
    "message_id": msg.id,
    "content": msg.content,
    "image_url": msg.image.url if msg.image else None,
    "video_url": msg.video.url if msg.video else None,
    "username": request.user.username,
})




@login_required
def room_list(request):
    """Отображает список всех комнат с доступами"""
    rooms = ChatRoom.objects.all()
    user = request.user

    room_access = {}
    for room in rooms:
        if not room.is_locked:
            room_access[room.id] = True
        elif user.is_superuser or user in room.allowed_users.all():
            room_access[room.id] = True
        else:
            room_access[room.id] = False

    return render(request, "mychat/room_list.html", {
        "rooms": rooms,
        "room_access": room_access
    })


@login_required
def room_detail(request, room_id):
    """Отображает конкретную комнату и обрабатывает отправку сообщений"""
    room = get_object_or_404(ChatRoom, id=room_id)
    user = request.user

    error_message = None

    # Проверяем доступ (staff и superuser всегда имеют доступ)
    if room.is_locked and not (request.user.is_superuser or request.user.is_staff or request.user in room.allowed_users.all()):
        logger.warning(f"Доступ запрещен: user={user.username}, room_id={room.id}")
        return render(request, "mychat/access_denied.html", {"room": room})
    logger.info(f"User {user.username} открыл комнату id={room.id}")


    # Проверка прав на удаление сообщений
    can_delete_messages = (
        request.user.is_superuser
        or request.user.is_staff
        or request.user.has_perm('mychat.delete_message')
    )

    users_in_room = User.objects.filter(message__room=room).distinct()
    
    if request.method == "POST":
        content = (request.POST.get("content") or "").strip()
        uploaded_file = request.FILES.get("media")
        if not content and not uploaded_file:
            logger.warning(f"User {user.username} попытался отправить пустое сообщение в room {room.id}")
            return JsonResponse({"success": False, "error": "Empty message"}, status=400)
        video_file = None
        image_file = None

        if uploaded_file:
            if uploaded_file.content_type.startswith("video/"):
                video_file = uploaded_file
            elif uploaded_file.content_type.startswith("image/"):
                image_file = uploaded_file
            else:
                logger.warning(f"User {request.user.username} попытался загрузить unsupported файл в room {room_id}")
                return JsonResponse({"success": False, "error": "Unsupported file type"}, status=400)

        if not content and not uploaded_file:
            logger.warning(f"User {request.user.username} попытался отправить пустое сообщение в room {room_id}")
            return JsonResponse({"success": False, "error": "Empty message"}, status=400)

        try:
            msg = Message(
                room=room,
                user=request.user,
                content=content,
                video=video_file,
                image=image_file
            )

            try:
                msg.full_clean()
                msg.save()
            except ValidationError as e:
                error_message = e.message_dict if hasattr(e, 'message_dict') else str(e)
                if isinstance(error_message, dict):
                    error_message = "; ".join([f"{field}: {', '.join(errors)}" for field, errors in error_message.items()])
                return JsonResponse({"success": False, "error": error_message}, status=400)

            logger.info(f"User {request.user.username} отправил сообщение в room {room_id} type: "
                        f"{'video' if video_file else 'image' if image_file else 'text'}")
        except Exception:
            logger.exception(f"Ошибка при создании сообщения в room {room_id} пользователем {request.user.username}")
            return JsonResponse({"success": False, "error": "Message creation failed"}, status=500)

        # Если это AJAX-запрос, возвращаем простой ответ
        if request.headers.get("x-requested-with") == "XMLHttpRequest":
            return JsonResponse({
        "success": True,
        "message_id": msg.id,
        "content": msg.content,
        "image_url": msg.image.url if msg.image else None,
        "video_url": msg.video.url if msg.video else None,
        "username": request.user.username,
    })

        return redirect("mychat:room_detail", room_id=room.id)

    # Получаем все сообщения
    messages_list = room.messages.all().order_by("created_at")

    # Онлайн пользователи за последние 5 минут
    five_minutes_ago = timezone.now() - timedelta(minutes=5)
    participants_online = UserProfile.objects.filter(
        last_seen__gte=five_minutes_ago
    ).select_related('user')

    # Частичный AJAX-запрос для обновления сообщений
    if request.GET.get('ajax'):
        return render(
            request,
            'mychat/messages_partial.html',
            {"messages": messages_list,
             "user": request.user}
        )

    return render(request, "mychat/room_detail.html", {
        "room": room,
        "messages": messages_list,
        "participants_online": participants_online,
        "can_delete_messages": can_delete_messages,
        "users": users_in_room,
        "error_message": error_message,
    })



@login_required
def create_room(request):
    if request.method == "POST":
        name = (request.POST.get("name") or "").strip()
        if not name:
            logger.warning(f"User {request.user.username} попытался создать комнату без имени")
            messages.error(request, "Введите название комнаты")
            return render(request, "mychat/create_room.html")
        room, created = ChatRoom.objects.get_or_create(name=name)
        if created:
            logger.info(f"Комната '{name}' создана пользователем {request.user.username}")
            messages.success(request, f"Комната '{name}' создана!")
        else:
            logger.info(f"Комната '{name}' уже существует (user={request.user.username})")
            messages.info(request, f"Комната '{name}' уже существует.")
        return redirect("mychat:room_list")

    return render(request, "mychat/create_room.html")


def is_admin(user):
    return user.is_superuser or user.is_staff


@login_required
@user_passes_test(is_admin)
def delete_room(request, room_id):
    """Удаление комнаты администратором"""
    room = get_object_or_404(ChatRoom, id=room_id)
    logger.info(f"Комната '{room.name}' (id={room.id}) удалена пользователем {request.user.username}")
    room.delete()
    messages.success(request, "Комната удалена")
    return redirect("mychat:room_list")


@login_required
@user_passes_test(is_admin)
def delete_message(request, message_id):
    """Удаление сообщения админом"""
    message = get_object_or_404(Message, id=message_id)
    logger.info(f"Сообщение id={message.id} удалено пользователем {request.user.username}")
    room_id = message.room.id
    message.delete()
    messages.success(request, "Сообщение удалено")
    return redirect("mychat:room_detail", room_id=room_id)    


@login_required
@user_passes_test(lambda u: u.is_staff or u.is_superuser)
def manage_access(request, room_id):
    """Настройка доступа пользователей к комнате"""
    room = get_object_or_404(ChatRoom, id=room_id)
    users = User.objects.exclude(is_superuser=True)

    if request.method == "POST":
        selected_users = request.POST.getlist("users")
        lock_room = request.POST.get("lock_room") == "on"

        if lock_room:
            room.is_locked = True
            room.allowed_users.clear()
            for user_id in selected_users:
                try:
                    user = User.objects.get(id=user_id)
                    room.allowed_users.add(user)
                except User.DoesNotExist:
                    logger.warning(f"Указан несуществующий user_id={user_id} при управлении доступом")
                    continue
            room.save()
            logger.info(f"Комната '{room.name}' (id={room.id}) заблокирована пользователем {request.user.username}")
            if request.user.is_staff:
                room.allowed_users.add(request.user)
                room.save()
                logger.info(f"Пользователю {request.user.username} добавлен доступ к комнате '{room.name}' (id={room.id})")
        else:
            room.is_locked = False
            room.allowed_users.clear()
            room.save()

        return redirect("mychat:room_list")

    return render(request, "mychat/manage_access.html", {
        "room": room,
        "users": users,
        "allowed_users": room.allowed_users.all()
    })
