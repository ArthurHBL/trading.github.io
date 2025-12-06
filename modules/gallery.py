
 FORUM WITH FIXED THUMBNAIL DISPLAY AND PERSISTENCE
# -------------------------

def render_image_gallery():
    """Main gallery - now paginated"""
    import streamlit as st
    st.session_state.gallery_page = 0
    st.title("📸 User Image Gallery (Paginated View)")
    render_image_gallery_paginated()

def decode_image_from_storage(item):
    """Decode image from storage format - placeholder implementation"""
    try:
        # This is a simplified version - you'll need to adapt based on your actual storage format
        if 'bytes_b64' in item:
            return base64.b64decode(item['bytes_b64'])
        return None
    except Exception:
        return None

# =====================================================================
# GALLERY PAGINATION CORE (placed before dashboard & main)
# =====================================================================
def get_gallery_images_count():
    """Get total count of gallery images"""
    if 'supabase_client' not in globals() or not supabase_client:
        return _cache_get("lk_gallery_count", 0)
    try:
        resp = supabase_client.table('gallery_images').select('id', count='exact').execute()
        if hasattr(resp, 'error') and resp.error:
            logging.error(f"Count error: {resp.error}")
            return _cache_get("lk_gallery_count", 0)
        count = getattr(resp, 'count', None) or (resp.data and len(resp.data)) or 0
        _cache_set("lk_gallery_count", count)
        return count
    except Exception as e:
        logging.error(f"Database count error: {e}")
        return _cache_get("lk_gallery_count", 0)

# USER IMAGE GALLERY - VIEW ONLY VERSION
# -------------------------
def render_user_image_gallery():
    """User image gallery with full database-backed pagination (FINAL)"""
    import streamlit as st

    # ---------- SAFETY: ensure needed session keys exist ----------
    if 'gallery_page' not in st.session_state:
        st.session_state.gallery_page = 0
    if 'gallery_per_page' not in st.session_state:
        st.session_state.gallery_per_page = 15
    if 'gallery_filter_author' not in st.session_state:
        st.session_state.gallery_filter_author = "All Authors"
    if 'gallery_filter_strategy' not in st.session_state:
        st.session_state.gallery_filter_strategy = "All Strategies"

    # ---------- HEADER ----------
    st.title("📸 Trading Analysis Image Gallery")
    st.markdown("View trading charts, analysis screenshots, and market insights shared by the community.")
    st.markdown("---")

    # Optional top tabs (Gallery / Statistics)
    tab1, tab2 = st.tabs(["🖼️ Image Gallery", "📊 Statistics"])
    with tab2:
        try:
            # Reuse your existing stats block
            if 'render_gallery_statistics_paginated' in globals():
                render_gallery_statistics_paginated()
            else:
                # Minimal stats fallback if function is not present
                total_images = get_gallery_images_count_filtered()
                st.metric("Total Images", total_images)
        except Exception as e:
            st.warning(f"Statistics unavailable: {e}")

    with tab1:
        # ---------- CONTROLS ----------
        st.subheader("🔍 Gallery Controls")
        c1, c2, c3, c4, c5 = st.columns(5)

        with c1:
            sort_by = st.selectbox(
                "Sort by:",
                ["newest", "oldest", "most_liked"],
                key="user_gallery_sort"
            )

        with c2:
            # Best-effort author list from any cached/known images in session
            authors_set = set(
                img.get('uploaded_by', 'Unknown')
                for img in (st.session_state.get('uploaded_images', []))
            )
            author_choice = st.selectbox(
                "Filter by Author:",
                ["All Authors"] + sorted(list(authors_set)),
                key="user_gallery_filter_author"
            )

        with c3:
            # If you keep strategies in st.session_state.STRATEGIES (dict), reuse it
            STRATEGIES = st.session_state.get('STRATEGIES', {})
            strategies_list = list(STRATEGIES.keys()) if isinstance(STRATEGIES, dict) else []
            strategy_choice = st.selectbox(
                "Filter by Strategy:",
                ["All Strategies"] + strategies_list,
                key="user_gallery_filter_strategy"
            )

        with c4:
            per_page = st.selectbox(
                "Per Page:",
                [10, 15, 20, 30],
                index=[10, 15, 20, 30].index(st.session_state.get("gallery_per_page", 15)) if st.session_state.get("gallery_per_page", 15) in [10, 15, 20, 30] else 1,
                key="user_gallery_per_page"
            )
            # Persist per-page
            st.session_state.gallery_per_page = per_page

        with c5:
            if st.button("🔄 Refresh", use_container_width=True, key="user_gallery_refresh"):
                st.rerun()

        # ---------- HANDLE FILTER CHANGES: reset to page 1 ----------
        # (We only reset if user changed the selection in this render cycle)
        if author_choice != st.session_state.get("_last_user_author_choice"):
            st.session_state.gallery_page = 0
            st.session_state._last_user_author_choice = author_choice
            st.rerun()
        if strategy_choice != st.session_state.get("_last_user_strategy_choice"):
            st.session_state.gallery_page = 0
            st.session_state._last_user_strategy_choice = strategy_choice
            st.rerun()

        st.markdown("---")

        # ---------- TOTAL COUNT ----------
        filter_author = None if author_choice == "All Authors" else author_choice
        filter_strategy = None if strategy_choice == "All Strategies" else strategy_choice

        with st.spinner("📊 Counting images..."):
            total_images = get_gallery_images_count_filtered(
                filter_author=filter_author,
                filter_strategy=filter_strategy
            )

        if total_images == 0:
            st.warning("🖼️ **No images found** for the selected filters.")
            return

        total_pages = (total_images + per_page - 1) // per_page
        current_page = min(st.session_state.gallery_page, max(0, total_pages - 1))

        # ---------- STATS ----------
        st.subheader("📈 Gallery Statistics")
        sc1, sc2, sc3, sc4 = st.columns(4)
        with sc1: st.metric("Total Images", total_images)
        with sc2: st.metric("Total Pages", total_pages)
        with sc3: st.metric("Current Page", current_page + 1)
        with sc4:
            start_num = current_page * per_page + 1
            end_num = min((current_page + 1) * per_page, total_images)
            st.metric("Showing", f"{start_num}-{end_num}")

        st.markdown("---")

        # ---------- TOP NAV ----------
        st.subheader("📄 Page Navigation")
        n1, n2, n3, n4, n5 = st.columns(5)

        with n1:
            if st.button("⏮️ First Page", use_container_width=True, key="user_gallery_first_top"):
                st.session_state.gallery_page = 0
                st.rerun()

        with n2:
            if current_page > 0:
                if st.button("◀️ Previous", use_container_width=True, key="user_gallery_prev_top"):
                    st.session_state.gallery_page = current_page - 1
                    st.rerun()
            else:
                st.button("◀️ Previous", use_container_width=True, disabled=True, key="user_gallery_prev_top_disabled")

        with n3:
            jump_page = st.number_input(
                "Go to Page:",
                min_value=1,
                max_value=max(1, total_pages),
                value=current_page + 1,
                key="user_gallery_jump"
            ) - 1
            if jump_page != current_page:
                st.session_state.gallery_page = max(0, min(jump_page, total_pages - 1))
                st.rerun()

        with n4:
            if current_page < total_pages - 1:
                if st.button("Next ▶️", use_container_width=True, key="user_gallery_next_top"):
                    st.session_state.gallery_page = current_page + 1
                    st.rerun()
            else:
                st.button("Next ▶️", use_container_width=True, disabled=True, key="user_gallery_next_top_disabled")

        with n5:
            if st.button("⏭️ Last Page", use_container_width=True, key="user_gallery_last_top"):
                st.session_state.gallery_page = total_pages - 1
                st.rerun()

        st.markdown("---")

        # ---------- PAGE DATA ----------
        with st.spinner("📥 Loading images..."):
            page_images = get_gallery_images_paginated(
                page=current_page,
                per_page=per_page,
                sort_by=sort_by,
                filter_author=filter_author,
                filter_strategy=filter_strategy
            )

        if not page_images:
            st.warning("⚠️ Failed to load images for this page.")
            if current_page > 0:
                st.session_state.gallery_page = 0
                st.rerun()
            return

        # Save current page images (if your viewer uses this)
        st.session_state.current_page_images = page_images

        # ---------- GRID ----------
        st.subheader(f"📸 Page {current_page + 1} Images")
        cols = st.columns(3)
        for idx, img_data in enumerate(page_images):
            col = cols[idx % 3]
            with col:
                # Use user card if you have one; otherwise reuse the generic card
                if 'render_user_image_card_paginated' in globals():
                    render_user_image_card_paginated(img_data, current_page, idx)
                else:
                    render_image_card_paginated(img_data, current_page, idx)

        st.markdown("---")

        # ---------- BOTTOM NAV ----------
        st.subheader("📄 Bottom Navigation")
        b1, b2, b3, b4, b5 = st.columns(5)

        with b1:
            if st.button("⏮️ First", use_container_width=True, key="user_gallery_first_bottom"):
                st.session_state.gallery_page = 0
                st.rerun()

        with b2:
            if current_page > 0:
                if st.button("◀️ Prev", use_container_width=True, key="user_gallery_prev_bottom"):
                    st.session_state.gallery_page = current_page - 1
                    st.rerun()
            else:
                st.button("◀️ Prev", use_container_width=True, disabled=True, key="user_gallery_prev_bottom_disabled")

        with b3:
            st.write(f"**Page {current_page + 1}/{total_pages}**")

        with b4:
            if current_page < total_pages - 1:
                if st.button("Next ▶️", use_container_width=True, key="user_gallery_next_bottom"):
                    st.session_state.gallery_page = current_page + 1
                    st.rerun()
            else:
                st.button("Next ▶️", use_container_width=True, disabled=True, key="user_gallery_next_bottom_disabled")

        with b5:
            if st.button("⏭️ Last", use_container_width=True, key="user_gallery_last_bottom"):
                st.session_state.gallery_page = total_pages - 1
                st.rerun()

        st.markdown("---")
        st.caption(f"✅ Displaying images {start_num}-{end_num} of {total_images} total")

def render_user_image_card_paginated(img_data, page_num, index):
    """Render individual image card - CLEAN IMAGE WITH DATE AND SMALL INFO"""
    try:
        # Get image bytes
        image_bytes = None
        if 'bytes' in img_data:
            image_bytes = img_data['bytes']
        elif 'bytes_b64' in img_data:
            image_bytes = base64.b64decode(img_data['bytes_b64'])
        
        if image_bytes:
            st.image(
                image_bytes,
                use_container_width=True,
                caption=None
            )
        else:
            st.warning("🖼️ Image data not available")
    except Exception as e:
        st.error(f"❌ Error displaying image")
    
    # Date and Download button row
    col1, col2 = st.columns([2, 1])
    
    with col1:
        timestamp = img_data.get('timestamp', '')
        if timestamp:
            try:
                upload_time = datetime.fromisoformat(timestamp).strftime("%m/%d/%Y")
                st.caption(f"📅 {upload_time}")
            except:
                st.caption(f"📅 {timestamp[:10]}")
        else:
            st.caption("📅 Unknown date")
    
    with col2:
        try:
            image_bytes = None
            if 'bytes' in img_data:
                image_bytes = img_data['bytes']
            elif 'bytes_b64' in img_data:
                image_bytes = base64.b64decode(img_data['bytes_b64'])
            
            if image_bytes:
                b64_img = base64.b64encode(image_bytes).decode()
                file_format = get_image_format_safe(img_data).lower()
                file_name = img_data.get('name', f'image_{index}')
                href = f'<a href="data:image/{file_format};base64,{b64_img}" download="{file_name}.{file_format}"><button style="width:100%; padding:6px; background:#4CAF50; color:white; border:none; border-radius:4px; cursor:pointer; font-size:12px; font-weight:bold;">⬇️ Download</button></a>'
                st.markdown(href, unsafe_allow_html=True)
        except Exception as e:
            st.button("⬇️ Download", disabled=True, use_container_width=True)
    
    st.divider()

def render_user_image_card(img_data, index):
    """Render individual image card for users - UPDATED FOR PAGINATION"""
    with st.container():
        # Display image at 50% width for better visibility
        col_image, col_info = st.columns([1.5, 1])  # 60% image, 40% info

        with col_image:
            try:
                # Check if we have bytes data in the expected format
                image_bytes = None
                if 'bytes' in img_data:
                    image_bytes = img_data['bytes']
                elif 'bytes_b64' in img_data:
                    image_bytes = base64.b64decode(img_data['bytes_b64'])
                
                if image_bytes:
                    st.image(
                        image_bytes,
                        use_container_width=True,
                        caption=img_data.get('name', 'Unnamed Image')
                    )
                else:
                    st.warning("📷 Image data not available")
            except Exception as e:
                st.error(f"❌ Error displaying image: {str(e)}")
                st.info("Image format may not be supported.")

        with col_info:
            # Image info on the right side
            st.markdown(f"**{img_data.get('name', 'Unnamed Image')}**")
            st.divider()

            # Description
            description = img_data.get('description', '')
            if description:
                preview = description[:100] + "..." if len(description) > 100 else description
                st.caption(f"📝 {preview}")
            else:
                st.caption("No description")

            # Strategy tags
            strategies = img_data.get('strategies', [])
            if strategies:
                st.caption(f"🏷️ **Strategies:**")
                for strategy in strategies[:3]:
                    st.caption(f"  • {strategy}")
                if len(strategies) > 3:
                    st.caption(f"  +{len(strategies) - 3} more")

            st.divider()

            # Metadata
            st.caption(f"👤 By: **{img_data.get('uploaded_by', 'Unknown')}**")
            timestamp = img_data.get('timestamp', '')
            if timestamp:
                try:
                    upload_time = datetime.fromisoformat(timestamp).strftime("%m/%d/%Y %H:%M")
                    st.caption(f"📅 {upload_time}")
                except:
                    st.caption(f"📅 {timestamp}")

            st.divider()

            # Interaction buttons - FULL WIDTH for better UX
            col_like, col_view = st.columns(2)

            with col_like:
                if st.button("❤️ Like", key=f"user_like_{index}_{img_data.get('id', index)}", use_container_width=True):
                    # Note: Like functionality would need to be implemented in the database
                    st.info("Like functionality requires database update implementation")
                    # img_data['likes'] = img_data.get('likes', 0) + 1
                    # save_gallery_images(st.session_state.uploaded_images)
                    # st.rerun()

            with col_view:
                if st.button("🖼️ Fullscreen", key=f"user_view_{index}_{img_data.get('id', index)}", use_container_width=True):
                    st.session_state.current_image_index = index
                    st.session_state.current_page_images = images  # Store current page images
                    st.session_state.image_viewer_mode = True
                    st.rerun()

            # Like count and download
            col_count, col_download = st.columns(2)
            with col_count:
                likes = img_data.get('likes', 0)
                st.metric("Likes", likes, label_visibility="collapsed")

            with col_download:
                try:
                    # Get image bytes for download
                    image_bytes = None
                    if 'bytes' in img_data:
                        image_bytes = img_data['bytes']
                    elif 'bytes_b64' in img_data:
                        image_bytes = base64.b64decode(img_data['bytes_b64'])
                    
                    if image_bytes:
                        b64_img = base64.b64encode(image_bytes).decode()
                        file_format = get_image_format_safe(img_data).lower()
                        file_name = img_data.get('name', f'image_{index}')
                        href = f'<a href="data:image/{file_format};base64,{b64_img}" download="{file_name}.{file_format}" style="text-decoration: none;">'
                        st.markdown(f'{href}<button style="background-color: #4CAF50; color: white; border: none; padding: 8px; text-align: center; text-decoration: none; display: inline-block; font-size: 12px; cursor: pointer; border-radius: 4px; width: 100%;">⬇️ Download</button></a>', unsafe_allow_html=True)
                    else:
                        st.caption("Download unavailable")
                except Exception as e:
                    st.caption("Download unavailable")

        st.markdown("---")

def render_image_viewer():
    """Image viewer for both admin and user galleries"""
    if not hasattr(st.session_state, 'current_page_images') or not st.session_state.current_page_images:
        st.warning("No images to display")
        st.session_state.image_viewer_mode = False
        st.rerun()
        return

    current_images = st.session_state.current_page_images
    current_index = st.session_state.current_image_index
    
    if current_index >= len(current_images):
        st.session_state.current_image_index = 0
        current_index = 0

    img_data = current_images[current_index]

    # Header with navigation
    col1, col2, col3, col4, col5 = st.columns([1, 1, 2, 1, 1])
    
    with col1:
        if st.button("⬅️ Back", use_container_width=True, key="viewer_back"):
            st.session_state.image_viewer_mode = False
            st.rerun()
            
    with col2:
        if st.button("◀️ Previous", use_container_width=True, disabled=current_index == 0, key="viewer_prev"):
            st.session_state.current_image_index = max(0, current_index - 1)
            st.rerun()
            
    with col3:
        st.markdown(f"### {img_data.get('name', 'Image Viewer')}")
        st.caption(f"Image {current_index + 1} of {len(current_images)}")
        
    with col4:
        if st.button("Next ▶️", use_container_width=True, disabled=current_index >= len(current_images) - 1, key="viewer_next"):
            st.session_state.current_image_index = min(len(current_images) - 1, current_index + 1)
            st.rerun()
            
    with col5:
        if st.button("📋 Close", use_container_width=True, key="viewer_close"):
            st.session_state.image_viewer_mode = False
            st.rerun()

    st.markdown("---")

    # Display the image at full width
    try:
        # Get image bytes
        image_bytes = None
        if 'bytes' in img_data:
            image_bytes = img_data['bytes']
        elif 'bytes_b64' in img_data:
            image_bytes = base64.b64decode(img_data['bytes_b64'])
        
        if image_bytes:
            st.image(image_bytes, use_container_width=True, caption=img_data.get('name', ''))
        else:
            st.error("❌ Unable to load image data")
    except Exception as e:
        st.error(f"❌ Error displaying image: {str(e)}")

    # Image details
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Image Details")
        st.write(f"**Name:** {img_data.get('name', 'N/A')}")
        st.write(f"**Uploaded by:** {img_data.get('uploaded_by', 'N/A')}")
        st.write(f"**Format:** {img_data.get('format', 'N/A')}")
        
        timestamp = img_data.get('timestamp', '')
        if timestamp:
            try:
                upload_time = datetime.fromisoformat(timestamp).strftime("%Y-%m-%d %H:%M:%S")
                st.write(f"**Uploaded:** {upload_time}")
            except:
                st.write(f"**Uploaded:** {timestamp}")
                
        st.write(f"**Likes:** {img_data.get('likes', 0)}")

    with col2:
        st.subheader("Description & Strategies")
        description = img_data.get('description', '')
        if description:
            st.write(description)
        else:
            st.info("No description provided")
            
        strategies = img_data.get('strategies', [])
        if strategies:
            st.write("**Related Strategies:**")
            for strategy in strategies:
                st.write(f"• {strategy}")
        else:
            st.info("No strategies tagged")

    # Download button
    st.markdown("---")
    try:
        image_bytes = None
        if 'bytes' in img_data:
            image_bytes = img_data['bytes']
        elif 'bytes_b64' in img_data:
            image_bytes = base64.b64decode(img_data['bytes_b64'])
            
        if image_bytes:
            b64_img = base64.b64encode(image_bytes).decode()
            file_format = get_image_format_safe(img_data).lower()
            file_name = img_data.get('name', f'image_{current_index}')
            href = f'<a href="data:image/{file_format};base64,{b64_img}" download="{file_name}.{file_format}" style="text-decoration: none;">'
            st.markdown(f'{href}<button style="background-color: #4CAF50; color: white; border: none; padding: 12px 24px; text-align: center; text-decoration: none; display: inline-block; font-size: 16px; margin: 4px 2px; cursor: pointer; border-radius: 4px; width: 100%;">⬇️ Download Full Resolution Image</button></a>', unsafe_allow_html=True)
    except Exception as e:
        st.error("Download unavailable")


 AND DISPLAY COMPONENTS - FIXED VERSION
# -------------------------
def render_strategy_indicator_image_upload(strategy_name, indicator_name):
    """Render image upload for a specific strategy indicator - FULL WIDTH"""
    st.subheader(f"🖼️ {indicator_name} - Chart Image")

    # Check if there's already an image for this indicator
    existing_image = get_strategy_indicator_image(strategy_name, indicator_name)

    if existing_image:
        st.success("✅ Image already uploaded for this indicator")

        # Display the existing image at FULL WIDTH
        st.markdown(f"**Current {indicator_name} Chart:**")

        # Display at 75% width (fixed size that works)
        col_empty, col_image, col_empty2 = st.columns([1, 3, 1])
        with col_image:
            st.image(
                existing_image['bytes'],
                use_container_width=True,
                caption=f"{indicator_name} Chart"
            )

        # Image info
        col1, col2, col3 = st.columns(3)
        with col1:
            st.caption(f"📤 Uploaded by: {existing_image['uploaded_by']}")
        with col2:
            st.caption(f"📅 {datetime.fromisoformat(existing_image['timestamp']).strftime('%Y-%m-%d %H:%M')}")
        with col3:
            st.caption(f"📋 Format: {existing_image['format']}")

        # Action buttons
        col_v, col_r = st.columns(2)
        with col_v:
            if st.button("🖼️ Full View", key=f"full_view_{strategy_name}_{indicator_name}", use_container_width=True):
                st.session_state.current_strategy_indicator_image = existing_image
                st.session_state.strategy_indicator_viewer_mode = True
                st.session_state.current_strategy_indicator = f"{strategy_name}_{indicator_name}"
                st.rerun()

        with col_r:
            if st.button("🗑️ Remove", key=f"remove_{strategy_name}_{indicator_name}", use_container_width=True):
                success = delete_strategy_indicator_image(strategy_name, indicator_name)
                if success:
                    st.success("✅ Image removed!")
                    st.rerun()
                else:
                    st.error("❌ Error removing image")

    # Image upload section
    st.markdown("---")
    st.write("**Upload New Chart Image:**")

    uploaded_file = st.file_uploader(
        f"Upload chart image for {indicator_name}",
        type=['png', 'jpg', 'jpeg', 'gif', 'bmp'],
        key=f"upload_{strategy_name}_{indicator_name}"
    )

    if uploaded_file is not None:
        # Display preview at FULL WIDTH
        st.markdown("**Preview:**")

        col_empty, col_preview, col_empty2 = st.columns([1, 3, 1])
        with col_preview:
            st.image(uploaded_file, use_container_width=True)

        # Upload button
        if st.button("💾 Save Image to Indicator", key=f"save_{strategy_name}_{indicator_name}", use_container_width=True):
            # Read and process the image
            image = Image.open(uploaded_file)
            img_bytes = io.BytesIO()

            # Use the correct format for saving
            if image.format:
                image.save(img_bytes, format=image.format)
            else:
                image.save(img_bytes, format='PNG')

            # Create image data with all required fields
            image_data = {
                'name': f"{strategy_name}_{indicator_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                'bytes': img_bytes.getvalue(),
                'format': image.format if image.format else 'PNG',
                'uploaded_by': st.session_state.user['username'],
                'timestamp': datetime.now().isoformat()
            }

            # Save the image
            success = save_strategy_indicator_image(strategy_name, indicator_name, image_data)
            if success:
                st.success("✅ Image saved successfully!")
                st.balloons()
                time.sleep(1)
                st.rerun()
            else:
                st.error("❌ Error saving image")

def render_strategy_indicator_image_viewer():
    """Viewer for strategy indicator images"""
    if not hasattr(st.session_state, 'current_strategy_indicator_image') or not st.session_state.current_strategy_indicator_image:
        st.warning("No image to display")
        st.session_state.strategy_indicator_viewer_mode = False
        st.rerun()
        return

    img_data = st.session_state.current_strategy_indicator_image

    # Header
    col1, col2, col3 = st.columns([1, 2, 1])
    with col1:
        if st.button("⬅️ Back", use_container_width=True, key="strategy_image_back"):
            st.session_state.strategy_indicator_viewer_mode = False
            st.rerun()

    with col2:
        st.markdown(f"### {img_data['strategy_name']} - {img_data['indicator_name']}")
        st.caption(f"Uploaded by: {img_data['uploaded_by']} | {datetime.fromisoformat(img_data['timestamp']).strftime('%Y-%m-%d %H:%M')}")

    with col3:
        if st.button("📋 Close", use_container_width=True, key="strategy_image_close"):
            st.session_state.strategy_indicator_viewer_mode = False
            st.rerun()

    st.markdown("---")

    # Main image display
    st.image(img_data['bytes'], use_container_width=True)

    # Download button
    st.markdown("---")
    try:
        b64_img = base64.b64encode(img_data['bytes']).decode()
        href = f'<a href="data:image/{img_data["format"].lower()};base64,{b64_img}" download="{img_data["name"]}" style="text-decoration: none;">'
        st.markdown(f'{href}<button style="background-color: #4CAF50; color: white; border: none; padding: 10px 20px; text-align: center; text-decoration: none; display: inline-block; font-size: 16px; cursor: pointer; border-radius: 4px; width: 100%;">⬇️ Download Image</button></a>', unsafe_allow_html=True)
    except Exception as e:
        st.error("Download unavailable")

def display_strategy_indicator_images_user(strategy_name):
    """Display strategy indicator images for users (view only) - FULL WIDTH"""
    if strategy_name not in st.session_state.strategy_indicator_images:
        return

    st.subheader("📊 Strategy Charts")

    indicators_with_images = st.session_state.strategy_indicator_images[strategy_name]

    if not indicators_with_images:
        st.info("No chart images available for this strategy yet.")
        return

    # Display images ONE PER ROW at FULL WIDTH
    for indicator_name, img_data in indicators_with_images.items():
        with st.container():
            st.markdown(f"#### **{indicator_name}**")

            # Display at full width
            # Display at 75% width (fixed size that works)
            col_empty, col_image, col_empty2 = st.columns([1, 3, 1])
            with col_image:
                st.image(
                    img_data['bytes'],
                    use_container_width=True,
                    caption=f"{indicator_name} Chart"
                )

            # Image info below
            col1, col2, col3 = st.columns(3)
            with col1:
                st.caption(f"📤 Uploaded by: {img_data['uploaded_by']}")
            with col2:
                st.caption(f"📅 {datetime.fromisoformat(img_data['timestamp']).strftime('%Y-%m-%d %H:%M')}")
            with col3:
                st.caption(f"📋 Format: {img_data['format']}")

            # Action buttons
            col_a, col_b = st.columns(2)
            with col_a:
                if st.button("🖼️ Fullscreen", key=f"user_view_strat_{strategy_name}_{indicator_name}", use_container_width=True):
                    st.session_state.current_strategy_indicator_image = img_data
                    st.session_state.strategy_indicator_viewer_mode = True
                    st.session_state.current_strategy_indicator = f"{strategy_name}_{indicator_name}"
                    st.rerun()
            with col_b:
                try:
                    b64_img = base64.b64encode(img_data['bytes']).decode()
                    href = f'<a href="data:image/{img_data["format"].lower()};base64,{b64_img}" download="{img_data["name"]}" style="text-decoration: none;">'
                    st.markdown(f'{href}<button style="background-color: #4CAF50; color: white; border: none; padding: 8px 12px; text-align: center; text-decoration: none; display: inline-block; font-size: 12px; cursor: pointer; border-radius: 4px; width: 100%;">⬇️ Download</button></a>', unsafe_allow_html=True)
                except:
                    st.button("⬇️ Download", disabled=True, use_container_width=True)

            st.markdown("---")

# -------------------------
# FIXED: USER PASSWORD CHANGE FUNCTIONALITY
# -------------------------
def render_user_password_change():
    """Allow users to change their own password"""
    st.subheader("🔐 Change Password")

    with st.form("user_password_change_form"):
        current_password = st.text_input("Current Password", type="password",
                                        placeholder="Enter your current password",
                                        key="user_current_password")
        new_password = st.text_input("New Password", type="password",
                                    placeholder="Enter new password (min 8 characters)",
                                    key="user_new_password")
        confirm_password = st.text_input("Confirm New Password", type="password",
                                        placeholder="Confirm new password",
                                        key="user_confirm_password")

        col1, col2 = st.columns(2)
        with col1:
            submitted = st.form_submit_button("✅ Change Password", use_container_width=True)
        with col2:
            if st.form_submit_button("❌ Cancel", use_container_width=True):
                st.session_state.show_user_password_change = False
                st.rerun()

        if submitted:
            if not current_password or not new_password or not confirm_password:
                st.error("❌ Please fill in all password fields")
            elif new_password != confirm_password:
                st.error("❌ New passwords do not match")
            elif len(new_password) < 8:
                st.error("❌ New password must be at least 8 characters")
            else:
                success, message = user_manager.change_own_password(
                    st.session_state.user['username'],
                    current_password,
                    new_password
                )
                if success:
                    st.success(f"✅ {message}")
                    st.session_state.show_user_password_change = False
                    time.sleep(2)
                    st.rerun()
                else:
                    st.error(f"❌ {message}")

# -------------------------
# FIXED: USER ACCOUNT SETTINGS - REMOVED KEY PARAMETER FROM ST.METRIC
# -------------------------
def render_user_account_settings():
    """User account settings - FIXED VERSION with top back button only"""

    # ADDED: Back button at the top
    col_back, col_title = st.columns([1, 5])
    with col_back:
        if st.button("⬅️ Back to Dashboard", use_container_width=True, key="user_settings_back_top"):
            st.session_state.dashboard_view = 'main'
            st.rerun()

    with col_title:
        st.title("⚙️ Account Settings")

    user = st.session_state.user

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Profile Information")
        st.text_input("Full Name", value=user['name'], disabled=True, key="user_profile_name")
        st.text_input("Email", value=user['email'], disabled=True, key="user_profile_email")
        st.text_input("Username", value=user['username'], disabled=True, key="user_profile_username")

    with col2:
        st.subheader("Subscription Details")
        plan_name = Config.PLANS.get(user['plan'], {}).get('name', user['plan'].title())
        st.text_input("Current Plan", value=plan_name, disabled=True, key="user_plan")
        st.text_input("Expiry Date", value=user['expires'], disabled=True, key="user_expires")

        # FIXED: Removed the 'key' parameter from st.metric to fix the error
        days_left = (datetime.strptime(user['expires'], "%Y-%m-%d").date() - date.today()).days
        st.metric("Days Remaining", days_left)

    st.markdown("---")

    # Password change section
    if st.session_state.show_user_password_change:
        render_user_password_change()
    else:
        if st.button("🔑 Change Password", use_container_width=True, key="user_change_password_btn"):
            st.session_state.show_user_password_change = True
            st.rerun()

def render_premium_user_section():
    """Premium user section with membership options"""
    st.title("💎 Premium User")

    user = st.session_state.user
    current_plan = user['plan']
    plan_name = Config.PLANS.get(current_plan, {}).get('name', current_plan.title())

    # User status header
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Current Plan", plan_name)
    with col2:
        days_left = (datetime.strptime(user['expires'], "%Y-%m-%d").date() - date.today()).days
        st.metric("Days Remaining", days_left)
    with col3:
        if current_plan == 'premium':
            st.metric("Status", "Active ✅")
        else:
            st.metric("Status", "Trial ⏳")

    st.markdown("---")

    # Plan comparison
    st.subheader("📊 Plan Comparison")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### 🆓 Trial Plan")
        trial_plan = Config.PLANS['trial']
        st.write("**Features:**")
        st.write(f"• {trial_plan['strategies']} Trading Strategies")
        st.write(f"• {trial_plan['max_sessions']} Concurrent Session")
        st.write(f"• {trial_plan['duration']}-day access")
        st.write("• Basic Signal Access")
        st.write("• View-Only Gallery")
        st.write("• KAI Analysis View")
        st.write(f"• **Price: ${trial_plan['price']}/month**")

        if current_plan == 'trial':
            st.success("🎯 Your Current Plan")

    with col2:
        st.markdown("### 💎 Premium Plan")
        premium_plan = Config.PLANS['premium']
        st.write("**Premium Features:**")
        st.write(f"• {premium_plan['strategies']} Trading Strategies")
        st.write(f"• {premium_plan['max_sessions']} Concurrent Sessions")
        st.write(f"• {premium_plan['duration']}-day access")
        st.write("• Full Signal Access")
        st.write("• Upload & Download Gallery")
        st.write("• Enhanced KAI Analysis")
        st.write("• Priority Support")
        st.write(f"• **Starting at: ${premium_plan['price']}/month**")

        if current_plan == 'premium':
            st.success("🎉 Premium Member!")
        else:
            st.warning("Upgrade to unlock")

    st.markdown("---")

    # Action sections
    if current_plan == 'trial':
        render_become_member_section()
    else:
        render_renew_subscription_section()

    st.markdown("---")

    # Benefits showcase
    st.subheader("🚀 Premium Benefits")

    benefits_col1, benefits_col2, benefits_col3 = st.columns(3)

    with benefits_col1:
        st.markdown("""
        **📈 Enhanced Signals**
        - Full strategy access
        - Real-time updates
        - Advanced analytics
        - Export capabilities
        """)

    with benefits_col2:
        st.markdown("""
        **🖼️ Gallery Features**
        - Upload your charts
        - Download community images
        - Fullscreen viewer
        - Strategy tagging
        """)

    with benefits_col3:
        st.markdown("""
        **🧠 KAI AI Agent**
        - Enhanced analysis
        - DeepSeek AI integration
        - Historical archive
        - Export functionality
        """)

    # Support information
    st.markdown("---")
    st.info("""
    **💁 Need Help?**
    - Contact support: support@tradinganalysis.com
    - Billing questions: billing@tradinganalysis.com
    - Technical issues: tech@tradinganalysis.com
    """)

def render_become_member_section():
    """Section for trial users to become premium members - Ko-Fi Integration"""
    st.subheader("⭐ Become a Premium Member")

    st.success("""
    **Ready to upgrade?** Get full access to all premium features including enhanced signals,
    gallery uploads, and advanced KAI AI analysis.
    """)

    # Ko-Fi payment options with GREEN buttons
    st.markdown("### 💳 Choose Your Plan")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown("#### 1 Month")
        st.write("**$19**")
        st.write("• Flexible billing")
        st.write("• Cancel anytime")

        kofi_monthly = Config.KOFI_PREMIUM_MONTHLY_LINK
        st.markdown(
            f'<a href="{kofi_monthly}" target="_blank"><button style="background-color: #10B981; color: white; padding: 10px 20px; border: none; border-radius: 4px; cursor: pointer; width: 100%;">💳 Subscribe Now</button></a>',
            unsafe_allow_html=True
        )

    with col2:
        st.markdown("#### 3 Months")
        st.write("**$49**")
        st.write("• 3 months access")
        st.write("• Best for short-term")

        kofi_quarterly = Config.KOFI_PREMIUM_QUARTERLY_LINK
        st.markdown(
            f'<a href="{kofi_quarterly}" target="_blank"><button style="background-color: #10B981; color: white; padding: 10px 20px; border: none; border-radius: 4px; cursor: pointer; width: 100%;">💎 Subscribe Now</button></a>',
            unsafe_allow_html=True
        )

    with col3:
        st.markdown("#### 6 Months")
        st.write("**$97**")
        st.write("• 6 months access")
        st.write("• Extended access")

        kofi_semi_annual = Config.KOFI_PREMIUM_SEMI_ANNUAL_LINK
        st.markdown(
            f'<a href="{kofi_semi_annual}" target="_blank"><button style="background-color: #10B981; color: white; padding: 10px 20px; border: none; border-radius: 4px; cursor: pointer; width: 100%;">🚀 Subscribe Now</button></a>',
            unsafe_allow_html=True
        )

    with col4:
        st.markdown("#### 12 Months")
        st.write("**$179**")
        st.write("• 12 months access")
        st.write("• Long-term value")

        kofi_annual = Config.KOFI_PREMIUM_ANNUAL_LINK
        st.markdown(
            f'<a href="{kofi_annual}" target="_blank"><button style="background-color: #10B981; color: white; padding: 10px 20px; border: none; border-radius: 4px; cursor: pointer; width: 100%;">🏆 Subscribe Now</button></a>',
            unsafe_allow_html=True
        )

    # Important information
    st.markdown("---")
    st.info("""
    **🔐 Secure Payment Process:**
    - You'll be redirected to Ko-Fi's secure payment page
    - Multiple payment methods accepted (credit card, PayPal, Apple Pay, Google Pay)
    - Instant access after successful payment
    - Email receipt provided
    """)

    # Manual upgrade option for admin
    if st.session_state.user['plan'] == 'admin':
        st.markdown("---")
        st.warning("**Admin Manual Upgrade:**")
        if st.button("🔼 Manually Upgrade User to Premium", key="manual_upgrade"):
            success, message = user_manager.change_user_plan(st.session_state.user['username'], "premium")
            if success:
                st.session_state.user['plan'] = "premium"
                st.success("✅ User upgraded to premium!")
                st.rerun()

def render_renew_subscription_section():
    """Updated renewal section with Ko-Fi buttons"""
    st.subheader("🔄 Renew Your Subscription")

    user = st.session_state.user
    days_left = (datetime.strptime(user['expires'], "%Y-%m-%d").date() - date.today()).days

    if days_left > 7:
        st.success(f"✅ Your premium subscription is active! {days_left} days remaining.")
    elif days_left > 0:
        st.warning(f"⚠️ Your subscription expires in {days_left} days. Renew now to avoid interruption.")
    else:
        st.error("❌ Your subscription has expired. Renew to restore premium access.")

    # Ko-Fi renewal options with GREEN buttons
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown("#### 1 Month")
        st.write("**$19**")
        kofi_monthly = Config.KOFI_PREMIUM_MONTHLY_LINK
        st.markdown(
            f'<a href="{kofi_monthly}" target="_blank"><button style="background-color: #10B981; color: white; padding: 10px 20px; border: none; border-radius: 4px; cursor: pointer; width: 100%;">🔄 Renew</button></a>',
            unsafe_allow_html=True
        )

    with col2:
        st.markdown("#### 3 Months")
        st.write("**$49**")
        kofi_quarterly = Config.KOFI_PREMIUM_QUARTERLY_LINK
        st.markdown(
            f'<a href="{kofi_quarterly}" target="_blank"><button style="background-color: #10B981; color: white; padding: 10px 20px; border: none; border-radius: 4px; cursor: pointer; width: 100%;">🔄 Renew</button></a>',
            unsafe_allow_html=True
        )

    with col3:
        st.markdown("#### 6 Months")
        st.write("**$97**")
        kofi_semi_annual = Config.KOFI_PREMIUM_SEMI_ANNUAL_LINK
        st.markdown(
            f'<a href="{kofi_semi_annual}" target="_blank"><button style="background-color: #10B981; color: white; padding: 10px 20px; border: none; border-radius: 4px; cursor: pointer; width: 100%;">🔄 Renew</button></a>',
            unsafe_allow_html=True
        )

    with col4:
        st.markdown("#### 12 Months")
        st.write("**$179**")
        kofi_annual = Config.KOFI_PREMIUM_ANNUAL_LINK
        st.markdown(
            f'<a href="{kofi_annual}" target="_blank"><button style="background-color: #10B981; color: white; padding: 10px 20px; border: none; border-radius: 4px; cursor: pointer; width: 100%;">🔄 Renew</button></a>',
            unsafe_allow_html=True
        )

    st.markdown("---")
    st.subheader("⚙️ Subscription Settings")
    col5, col6 = st.columns(2)
    with col5:
        st.info("💡 Ko-Fi handles automatic renewals. Check your Ko-Fi dashboard for subscription settings.")
    with col6:
        st.info("📧 You'll receive renewal reminders via email before expiry.")

# -------------------------
# ENHANCED PREMIUM SIGNAL DASHBOARD WITH STRATEGY INDICATOR IMAGES - FIXED VERSION
# -------------------------
def render_premium_signal_dashboard():
    """Premium signal dashboard where admin can edit signals with full functionality"""

    # User-specific data isolation
    user = st.session_state.user
    user_data_key = f"{user['username']}_data"
    if user_data_key not in st.session_state.user_data:
        st.session_state.user_data[user_data_key] = {
            "saved_analyses": {},
            "favorite_strategies": [],
            "performance_history": [],
            "recent_signals": []
        }

    data = st.session_state.user_data[user_data_key]

    # Use session state strategy analyses data - FIXED: Now using session state
    strategy_data = st.session_state.strategy_analyses_data

    # Date navigation
    start_date = date(2025, 8, 9)

    # Get date from URL parameters or session state
    query_params = st.query_params
    current_date_str = query_params.get("date", "")

    if current_date_str:
        try:
            analysis_date = datetime.strptime(current_date_str, "%Y-%m-%d").date()
            st.session_state.analysis_date = analysis_date
        except ValueError:
            analysis_date = st.session_state.get('analysis_date', date.today())
    else:
        analysis_date = st.session_state.get('analysis_date', date.today())

    # Ensure analysis_date is not before start_date
    if analysis_date < start_date:
        analysis_date = start_date
        st.session_state.analysis_date = start_date

    # Get daily strategies and cycle day
    daily_strategies, cycle_day = get_daily_strategies(analysis_date)

    # FIXED: Auto-select first strategy when date changes or no strategy selected
    if (st.session_state.get('last_analysis_date') != analysis_date or
        st.session_state.selected_strategy is None or
        st.session_state.selected_strategy not in daily_strategies):
        st.session_state.selected_strategy = daily_strategies[0]
        st.session_state.last_analysis_date = analysis_date

    selected_strategy = st.session_state.selected_strategy

    # FIXED: Clean sidebar with proper layout - 5-DAY CYCLE FIRST, then STRATEGY SELECTION, then SIGNAL ACTIONS
    with st.sidebar:
        st.title("🎛️ Admin Signal Control Panel")

        # Admin profile section
        st.markdown("---")
        st.write(f"👑 {user['name']}")
        st.success("🛠️ Admin Signal Editor")

        st.markdown("---")

        # 5-Day Cycle System - MOVED TO TOP (FIRST SECTION)
        st.subheader("📅 5-Day Cycle")

        # Display current date
        st.markdown(f"**Current Date:** {analysis_date.strftime('%m/%d/%Y')}")

        # Date navigation
        col1, col2 = st.columns(2)
        with col1:
            if st.button("◀️ Prev Day", use_container_width=True, key="premium_prev_day_btn"):
                new_date = analysis_date - timedelta(days=1)
                if new_date >= start_date:
                    st.query_params["date"] = new_date.strftime("%Y-%m-%d")
                    st.rerun()
                else:
                    st.warning("Cannot go before start date")
        with col2:
            if st.button("Next Day ▶️", use_container_width=True, key="premium_next_day_btn"):
                new_date = analysis_date + timedelta(days=1)
                st.query_params["date"] = new_date.strftime("%Y-%m-%d")
                st.rerun()

        # Quick date reset button
        if st.button("🔄 Today", use_container_width=True, key="premium_today_btn"):
            st.query_params["date"] = date.today().strftime("%Y-%m-%d")
            st.rerun()

        # Cycle information
        st.info(f"**Day {cycle_day} of 5-day cycle**")

        st.markdown("---")

        # Strategy selection - MOVED TO SECOND SECTION (right after 5-day cycle)
        # CHANGED: Replace dropdown with clickable buttons
        st.subheader("🎯 Choose Strategy to Edit:")

        # Create clickable buttons for each strategy
        for strategy in daily_strategies:
            if st.button(
                f"📊 {strategy}",
                use_container_width=True,
                type="primary" if strategy == selected_strategy else "secondary",
                key=f"premium_strategy_{strategy}"
            ):
                st.session_state.selected_strategy = strategy
                st.rerun()

        st.markdown("---")

        # Signal Actions - MOVED TO THIRD SECTION (after strategy selection)
        st.subheader("📊 Signal Actions")

        if st.button("📈 Signal Dashboard", use_container_width=True, key="premium_nav_main"):
            st.session_state.dashboard_view = 'main'
            st.rerun()

        if st.button("📝 Edit Signals", use_container_width=True, key="premium_nav_notes"):
            st.session_state.dashboard_view = 'notes'
            st.rerun()

        if st.button("⚙️ Admin Settings", use_container_width=True, key="premium_nav_settings"):
            st.session_state.dashboard_view = 'settings'
            st.rerun()

        if st.button("🔄 Refresh Signals", use_container_width=True, key="premium_nav_refresh"):
            st.rerun()

        st.markdown("---")

        # Export functionality
        csv_bytes = generate_filtered_csv_bytes(strategy_data, analysis_date)
        st.subheader("📄 Export Data")
        st.download_button(
            label="⬇️ Download CSV",
            data=csv_bytes,
            file_name=f"strategy_analyses_{analysis_date.strftime('%Y%m%d')}.csv",
            mime="text/csv",
            use_container_width=True,
            key="premium_export_btn"
        )

        st.markdown("---")
        if st.button("🚪 Secure Logout", use_container_width=True, key="premium_logout_btn"):
            user_manager.logout(user['username'])
            st.session_state.user = None
            st.session_state.admin_dashboard_mode = None
            st.rerun()

    # Main dashboard content
    current_view = st.session_state.get('dashboard_view', 'main')

    if current_view == 'notes':
        render_admin_strategy_notes(strategy_data, daily_strategies, cycle_day, analysis_date, selected_strategy)
    elif current_view == 'settings':
        render_admin_account_settings()
    else:
        render_admin_trading_dashboard(data, user, daily_strategies, cycle_day, analysis_date, selected_strategy)

def render_admin_trading_dashboard(data, user, daily_strategies, cycle_day, analysis_date, selected_strategy):
    """Admin trading dashboard with editing capabilities"""
    st.title("📊 Admin Signal Dashboard")

    # Welcome and cycle info
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        st.success(f"👑 Welcome back, **{user['name']}**! You're in **Admin Signal Mode** with full editing access.")
    with col2:
        st.metric("Cycle Day", f"Day {cycle_day}/5")
    with col3:
        st.metric("Admin Mode", "Unlimited")

    st.markdown("---")

    # Progress indicators for today's strategies
    st.subheader("📋 Today's Strategy Progress")
    cols = st.columns(3)

    strategy_data = st.session_state.strategy_analyses_data
    for i, strategy in enumerate(daily_strategies):
        with cols[i]:
            strategy_completed = False
            if strategy in strategy_data:
                # Check if all indicators have notes for today
                today_indicators = [ind for ind, meta in strategy_data[strategy].items()
                                  if meta.get("analysis_date") == analysis_date.strftime("%Y-%m-%d")]
                if len(today_indicators) == len(STRATEGIES[strategy]):
                    strategy_completed = True

            if strategy_completed:
                st.success(f"✅ {strategy}")
            elif strategy == selected_strategy:
                st.info(f"📝 {strategy} (current)")
            else:
                st.warning(f"🕓 {strategy}")

    st.markdown("---")

    # Selected strategy analysis - ADMIN EDITING ENABLED
    # CHANGED: Removed " - ADMIN EDIT MODE" and added green BUY button
    col_header1, col_header2 = st.columns([3, 1])
    with col_header1:
        st.subheader(f"🔍 {selected_strategy} Analysis")
    with col_header2:
        st.button("🟢 BUY Strategy",
                 use_container_width=True,
                 key=f"buy_bundle_{selected_strategy}",
                 help="Purchase to use in TradingView")

    # REMOVED: Quick Analysis Notes section completely

    st.markdown("---")

    # NEW: Strategy indicator images section - FIXED: Now properly placed outside forms
    render_strategy_indicator_image_upload(selected_strategy, "Overview")

    st.markdown("---")

    # Detailed analysis button
    if st.button("📝 Open Detailed Analysis Editor", use_container_width=True, key="detailed_analysis_btn"):
        st.session_state.dashboard_view = 'notes'
        st.rerun()

    # Recent activity
    if data.get('saved_analyses'):
        st.markdown("---")
        st.subheader("📜 Recent Analyses")
        for strategy, analysis in list(data['saved_analyses'].items())[-3:]:
            with st.expander(f"{strategy} - {analysis['timestamp'].strftime('%H:%M')}"):
                st.write(f"**Tag:** {analysis['tag']} | **Type:** {analysis['type']}")
                st.write(analysis.get('note', 'No notes'))

def render_admin_strategy_notes(strategy_data, daily_strategies, cycle_day, analysis_date, selected_strategy):
    """Detailed strategy notes interface with full admin editing - UPDATED TYPE OPTIONS AND PROVIDER"""
    st.title("📝 Admin Signal Editor")

    # Header with cycle info
    col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
    with col1:
        st.subheader(f"Day {cycle_day} - {selected_strategy}")
    with col2:
        st.metric("Analysis Date", analysis_date.strftime("%m/%d/%Y"))
    with col3:
        st.button("🟢 BUY Strategy",
                 use_container_width=True,
                 key=f"buy_bundle_notes_{selected_strategy}",
                 help="Purchase to use in TradingView")
    with col4:
        if st.button("⬅️ Back to Dashboard", use_container_width=True, key="admin_back_dashboard_btn"):
            st.session_state.dashboard_view = 'main'
            st.rerun()

    st.markdown("---")

    # Notes Form - ADMIN VERSION WITH FULL ACCESS
    with st.form("admin_detailed_notes_form"):
        st.subheader(f"Admin Signal Editor - {selected_strategy}")

        # Load existing data for this strategy
        existing_data = strategy_data.get(selected_strategy, {})
        current_strategy_tag = next(iter(existing_data.values()), {}).get("strategy_tag", "Neutral")

        # UPDATED: Strategy Type with new lowercase options
        current_strategy_type = next(iter(existing_data.values()), {}).get("momentum", "Neutral reading")

        # Handle migration from old values to new values
        type_mapping = {
            "Momentum": "Momentum reading",
            "Extreme": "Extreme reading",
            "Not Defined": "Neutral reading",
            "MOMENTUM READING": "Momentum reading",
            "EXTREME READING": "Extreme reading",
            "NEUTRAL READING": "Neutral reading"
        }

        # Convert old values to new values
        if current_strategy_type in type_mapping:
            current_strategy_type = type_mapping[current_strategy_type]

        # Strategy-level settings
        col1, col2 = st.columns(2)
        with col1:
            strategy_tag = st.selectbox("Strategy Tag:", ["Neutral", "Buy", "Sell"],
                                      index=["Neutral","Buy","Sell"].index(current_strategy_tag),
                                      key="admin_strategy_tag")
        with col2:
            # UPDATED: New Type options in lowercase
            new_type_options = ["Neutral reading", "Extreme reading", "Momentum reading"]
            current_index = new_type_options.index(current_strategy_type) if current_strategy_type in new_type_options else 0
            strategy_type = st.selectbox("Strategy Type:", new_type_options,
                                       index=current_index,
                                       key="admin_strategy_type")

        st.markdown("---")

        # Indicator analysis in columns - ADMIN CAN EDIT ALL
        indicators = STRATEGIES[selected_strategy]
        col_objs = st.columns(3)

        for i, indicator in enumerate(indicators):
            col = col_objs[i % 3]
            key_note = f"note__{sanitize_key(selected_strategy)}__{sanitize_key(indicator)}"
            key_status = f"status__{sanitize_key(selected_strategy)}__{sanitize_key(indicator)}"

            existing = existing_data.get(indicator, {})
            default_note = existing.get("note", "")
            default_status = existing.get("status", "Open")

            with col.expander(f"**{indicator}** - ADMIN EDIT", expanded=False):
                st.text_area(
                    f"Analysis Notes",
                    value=default_note,
                    key=key_note,
                    height=140,
                    placeholder=f"Enter analysis for {indicator}..."
                )
                st.selectbox(
                    "Status",
                    ["Open", "In Progress", "Done", "Skipped"],
                    index=["Open", "In Progress", "Done", "Skipped"].index(default_status) if default_status in ["Open", "In Progress", "Done", "Skipped"] else 0,
                    key=key_status
                )

        # Save button
        submitted = st.form_submit_button("💾 Save All Signals (Admin)", use_container_width=True, key="admin_save_all_btn")
        if submitted:
            if selected_strategy not in st.session_state.strategy_analyses_data:
                st.session_state.strategy_analyses_data[selected_strategy] = {}

            for indicator in indicators:
                key_note = f"note__{sanitize_key(selected_strategy)}__{sanitize_key(indicator)}"
                key_status = f"status__{sanitize_key(selected_strategy)}__{sanitize_key(indicator)}"

                st.session_state.strategy_analyses_data[selected_strategy][indicator] = {
                    "note": st.session_state.get(key_note, ""),
                    "status": st.session_state.get(key_status, "Open"),
                    "momentum": strategy_type,  # This now stores the new lowercase type
                    "strategy_tag": strategy_tag,
                    "analysis_date": analysis_date.strftime("%Y-%m-%d"),
                    "last_modified": datetime.utcnow().isoformat() + "Z",
                    "modified_by": "KAI"  # CHANGED: from "admin" to "KAI"
                }

            # Save to Supabase
            save_data(st.session_state.strategy_analyses_data)
            st.success("✅ All signals saved successfully! (Admin Mode)")

    # FIXED: Strategy indicator images section - Now placed outside the main form
    st.markdown("---")
    st.subheader("🖼️ Strategy Indicator Images")

    # Display images for each indicator
    indicators = STRATEGIES[selected_strategy]
    col_objs = st.columns(3)

    for i, indicator in enumerate(indicators):
        col = col_objs[i % 3]
        with col:
            with st.expander(f"📊 {indicator} Chart", expanded=False):
                # FIXED: Call the image upload function outside any form
                render_strategy_indicator_image_upload(selected_strategy, indicator)

    # Display saved analyses
    st.markdown("---")
    st.subheader("📜 Saved Signals - ADMIN VIEW")

    view_options = ["Today's Focus"] + daily_strategies
    filter_strategy = st.selectbox("Filter by strategy:", view_options, index=0, key="admin_filter_strategy")

    if filter_strategy == "Today's Focus":
        strategies_to_show = daily_strategies
    else:
        strategies_to_show = [filter_strategy]

    color_map = {"Buy": "🟢 Buy", "Sell": "🔴 Sell", "Neutral": "⚪ Neutral"}

    for strat in strategies_to_show:
        if strat in strategy_data:
            st.markdown(f"### {strat}")
            inds = strategy_data.get(strat, {})
            if not inds:
                st.info("No saved signals for this strategy.")
                continue

            strategy_tag = next(iter(inds.values())).get("strategy_tag", "Neutral")
            st.markdown(f"**Strategy Tag:** {color_map.get(strategy_tag, strategy_tag)}")
            st.markdown("---")

            for ind_name, meta in inds.items():
                if meta.get("analysis_date") == analysis_date.strftime("%Y-%m-%d"):
                    momentum_type = meta.get("momentum", "neutral reading")
                    # Apply the same mapping for display
                    if momentum_type in type_mapping:
                        momentum_type = type_mapping[momentum_type]
                    status_icon = "✅ Done" if meta.get("status", "Open") == "Done" else "🕓 Open"
                    # CHANGED: Show "KAI" instead of the actual modified_by field
                    with st.expander(f"{ind_name} ({momentum_type}) — {status_icon} — Provider: KAI", expanded=False):
                        st.write(meta.get("note", "") or "_No notes yet_")
                        st.caption(f"Last updated: {meta.get('last_modified', 'N/A')}")

def render_admin_account_settings():
    """Admin account settings in premium mode - FIXED with top back button only"""

    # ADDED: Back button at the top
    col_back, col_title = st.columns([1, 5])
    with col_back:
        if st.button("⬅️ Back to Dashboard", use_container_width=True, key="admin_settings_back_top"):
            st.session_state.dashboard_view = 'main'
            st.rerun()

    with col_title:
        st.title("⚙️ Admin Settings - Premium Mode")

    user = st.session_state.user

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Admin Profile")
        st.text_input("Full Name", value=user['name'], disabled=True, key="admin_profile_name")
        st.text_input("Email", value=user['email'], disabled=True, key="admin_profile_email")
        st.text_input("Username", value=user['username'], disabled=True, key="admin_profile_username")

    with col2:
        st.subheader("Admin Privileges")
        st.text_input("Role", value="System Administrator", disabled=True, key="admin_role")
        st.text_input("Access Level", value="Full System Access", disabled=True, key="admin_access")
        st.text_input("Signal Editing", value="Enabled", disabled=True, key="admin_editing")

    st.markdown("---")
    st.subheader("Quick Actions")

    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("🛠️ Switch to Admin Dashboard", use_container_width=True, key="switch_admin_dash_btn"):
            st.session_state.admin_dashboard_mode = "admin"
            st.rerun()

    with col2:
        if st.button("📊 Refresh All Data", use_container_width=True, key="refresh_admin_data_btn"):
            user_manager.load_data()
            st.rerun()


 WITH FIXED THUMBNAIL DISPLAY AND PERSISTENCE
# -------------------------

def render_image_gallery():
    """Main gallery - now paginated"""
    import streamlit as st
    st.session_state.gallery_page = 0
    st.title("📸 User Image Gallery (Paginated View)")
    render_image_gallery_paginated()

def decode_image_from_storage(item):
    """Decode image from storage format - placeholder implementation"""
    try:
        # This is a simplified version - you'll need to adapt based on your actual storage format
        if 'bytes_b64' in item:
            return base64.b64decode(item['bytes_b64'])
        return None
    except Exception:
        return None

# =====================================================================
# GALLERY PAGINATION CORE (placed before dashboard & main)
# =====================================================================
def get_gallery_images_count():
    """Get total count of gallery images"""
    if 'supabase_client' not in globals() or not supabase_client:
        return _cache_get("lk_gallery_count", 0)
    try:
        resp = supabase_client.table('gallery_images').select('id', count='exact').execute()
        if hasattr(resp, 'error') and resp.error:
            logging.error(f"Count error: {resp.error}")
            return _cache_get("lk_gallery_count", 0)
        count = getattr(resp, 'count', None) or (resp.data and len(resp.data)) or 0
        _cache_set("lk_gallery_count", count)
        return count
    except Exception as e:
        logging.error(f"Database count error: {e}")
        return _cache_get("lk_gallery_count", 0)

# USER IMAGE GALLERY - VIEW ONLY VERSION
# -------------------------
def render_user_image_gallery():
    """User image gallery with full database-backed pagination (FINAL)"""
    import streamlit as st

    # ---------- SAFETY: ensure needed session keys exist ----------
    if 'gallery_page' not in st.session_state:
        st.session_state.gallery_page = 0
    if 'gallery_per_page' not in st.session_state:
        st.session_state.gallery_per_page = 15
    if 'gallery_filter_author' not in st.session_state:
        st.session_state.gallery_filter_author = "All Authors"
    if 'gallery_filter_strategy' not in st.session_state:
        st.session_state.gallery_filter_strategy = "All Strategies"

    # ---------- HEADER ----------
    st.title("📸 Trading Analysis Image Gallery")
    st.markdown("View trading charts, analysis screenshots, and market insights shared by the community.")
    st.markdown("---")

    # Optional top tabs (Gallery / Statistics)
    tab1, tab2 = st.tabs(["🖼️ Image Gallery", "📊 Statistics"])
    with tab2:
        try:
            # Reuse your existing stats block
            if 'render_gallery_statistics_paginated' in globals():
                render_gallery_statistics_paginated()
            else:
                # Minimal stats fallback if function is not present
                total_images = get_gallery_images_count_filtered()
                st.metric("Total Images", total_images)
        except Exception as e:
            st.warning(f"Statistics unavailable: {e}")

    with tab1:
        # ---------- CONTROLS ----------
        st.subheader("🔍 Gallery Controls")
        c1, c2, c3, c4, c5 = st.columns(5)

        with c1:
            sort_by = st.selectbox(
                "Sort by:",
                ["newest", "oldest", "most_liked"],
                key="user_gallery_sort"
            )

        with c2:
            # Best-effort author list from any cached/known images in session
            authors_set = set(
                img.get('uploaded_by', 'Unknown')
                for img in (st.session_state.get('uploaded_images', []))
            )
            author_choice = st.selectbox(
                "Filter by Author:",
                ["All Authors"] + sorted(list(authors_set)),
                key="user_gallery_filter_author"
            )

        with c3:
            # If you keep strategies in st.session_state.STRATEGIES (dict), reuse it
            STRATEGIES = st.session_state.get('STRATEGIES', {})
            strategies_list = list(STRATEGIES.keys()) if isinstance(STRATEGIES, dict) else []
            strategy_choice = st.selectbox(
                "Filter by Strategy:",
                ["All Strategies"] + strategies_list,
                key="user_gallery_filter_strategy"
            )

        with c4:
            per_page = st.selectbox(
                "Per Page:",
                [10, 15, 20, 30],
                index=[10, 15, 20, 30].index(st.session_state.get("gallery_per_page", 15)) if st.session_state.get("gallery_per_page", 15) in [10, 15, 20, 30] else 1,
                key="user_gallery_per_page"
            )
            # Persist per-page
            st.session_state.gallery_per_page = per_page

        with c5:
            if st.button("🔄 Refresh", use_container_width=True, key="user_gallery_refresh"):
                st.rerun()

        # ---------- HANDLE FILTER CHANGES: reset to page 1 ----------
        # (We only reset if user changed the selection in this render cycle)
        if author_choice != st.session_state.get("_last_user_author_choice"):
            st.session_state.gallery_page = 0
            st.session_state._last_user_author_choice = author_choice
            st.rerun()
        if strategy_choice != st.session_state.get("_last_user_strategy_choice"):
            st.session_state.gallery_page = 0
            st.session_state._last_user_strategy_choice = strategy_choice
            st.rerun()

        st.markdown("---")

        # ---------- TOTAL COUNT ----------
        filter_author = None if author_choice == "All Authors" else author_choice
        filter_strategy = None if strategy_choice == "All Strategies" else strategy_choice

        with st.spinner("📊 Counting images..."):
            total_images = get_gallery_images_count_filtered(
                filter_author=filter_author,
                filter_strategy=filter_strategy
            )

        if total_images == 0:
            st.warning("🖼️ **No images found** for the selected filters.")
            return

        total_pages = (total_images + per_page - 1) // per_page
        current_page = min(st.session_state.gallery_page, max(0, total_pages - 1))

        # ---------- STATS ----------
        st.subheader("📈 Gallery Statistics")
        sc1, sc2, sc3, sc4 = st.columns(4)
        with sc1: st.metric("Total Images", total_images)
        with sc2: st.metric("Total Pages", total_pages)
        with sc3: st.metric("Current Page", current_page + 1)
        with sc4:
            start_num = current_page * per_page + 1
            end_num = min((current_page + 1) * per_page, total_images)
            st.metric("Showing", f"{start_num}-{end_num}")

        st.markdown("---")

        # ---------- TOP NAV ----------
        st.subheader("📄 Page Navigation")
        n1, n2, n3, n4, n5 = st.columns(5)

        with n1:
            if st.button("⏮️ First Page", use_container_width=True, key="user_gallery_first_top"):
                st.session_state.gallery_page = 0
                st.rerun()

        with n2:
            if current_page > 0:
                if st.button("◀️ Previous", use_container_width=True, key="user_gallery_prev_top"):
                    st.session_state.gallery_page = current_page - 1
                    st.rerun()
            else:
                st.button("◀️ Previous", use_container_width=True, disabled=True, key="user_gallery_prev_top_disabled")

        with n3:
            jump_page = st.number_input(
                "Go to Page:",
                min_value=1,
                max_value=max(1, total_pages),
                value=current_page + 1,
                key="user_gallery_jump"
            ) - 1
            if jump_page != current_page:
                st.session_state.gallery_page = max(0, min(jump_page, total_pages - 1))
                st.rerun()

        with n4:
            if current_page < total_pages - 1:
                if st.button("Next ▶️", use_container_width=True, key="user_gallery_next_top"):
                    st.session_state.gallery_page = current_page + 1
                    st.rerun()
            else:
                st.button("Next ▶️", use_container_width=True, disabled=True, key="user_gallery_next_top_disabled")

        with n5:
            if st.button("⏭️ Last Page", use_container_width=True, key="user_gallery_last_top"):
                st.session_state.gallery_page = total_pages - 1
                st.rerun()

        st.markdown("---")

        # ---------- PAGE DATA ----------
        with st.spinner("📥 Loading images..."):
            page_images = get_gallery_images_paginated(
                page=current_page,
                per_page=per_page,
                sort_by=sort_by,
                filter_author=filter_author,
                filter_strategy=filter_strategy
            )

        if not page_images:
            st.warning("⚠️ Failed to load images for this page.")
            if current_page > 0:
                st.session_state.gallery_page = 0
                st.rerun()
            return

        # Save current page images (if your viewer uses this)
        st.session_state.current_page_images = page_images

        # ---------- GRID ----------
        st.subheader(f"📸 Page {current_page + 1} Images")
        cols = st.columns(3)
        for idx, img_data in enumerate(page_images):
            col = cols[idx % 3]
            with col:
                # Use user card if you have one; otherwise reuse the generic card
                if 'render_user_image_card_paginated' in globals():
                    render_user_image_card_paginated(img_data, current_page, idx)
                else:
                    render_image_card_paginated(img_data, current_page, idx)

        st.markdown("---")

        # ---------- BOTTOM NAV ----------
        st.subheader("📄 Bottom Navigation")
        b1, b2, b3, b4, b5 = st.columns(5)

        with b1:
            if st.button("⏮️ First", use_container_width=True, key="user_gallery_first_bottom"):
                st.session_state.gallery_page = 0
                st.rerun()

        with b2:
            if current_page > 0:
                if st.button("◀️ Prev", use_container_width=True, key="user_gallery_prev_bottom"):
                    st.session_state.gallery_page = current_page - 1
                    st.rerun()
            else:
                st.button("◀️ Prev", use_container_width=True, disabled=True, key="user_gallery_prev_bottom_disabled")

        with b3:
            st.write(f"**Page {current_page + 1}/{total_pages}**")

        with b4:
            if current_page < total_pages - 1:
                if st.button("Next ▶️", use_container_width=True, key="user_gallery_next_bottom"):
                    st.session_state.gallery_page = current_page + 1
                    st.rerun()
            else:
                st.button("Next ▶️", use_container_width=True, disabled=True, key="user_gallery_next_bottom_disabled")

        with b5:
            if st.button("⏭️ Last", use_container_width=True, key="user_gallery_last_bottom"):
                st.session_state.gallery_page = total_pages - 1
                st.rerun()

        st.markdown("---")
        st.caption(f"✅ Displaying images {start_num}-{end_num} of {total_images} total")

def render_user_image_card_paginated(img_data, page_num, index):
    """Render individual image card - CLEAN IMAGE WITH DATE AND SMALL INFO"""
    try:
        # Get image bytes
        image_bytes = None
        if 'bytes' in img_data:
            image_bytes = img_data['bytes']
        elif 'bytes_b64' in img_data:
            image_bytes = base64.b64decode(img_data['bytes_b64'])
        
        if image_bytes:
            st.image(
                image_bytes,
                use_container_width=True,
                caption=None
            )
        else:
            st.warning("🖼️ Image data not available")
    except Exception as e:
        st.error(f"❌ Error displaying image")
    
    # Date and Download button row
    col1, col2 = st.columns([2, 1])
    
    with col1:
        timestamp = img_data.get('timestamp', '')
        if timestamp:
            try:
                upload_time = datetime.fromisoformat(timestamp).strftime("%m/%d/%Y")
                st.caption(f"📅 {upload_time}")
            except:
                st.caption(f"📅 {timestamp[:10]}")
        else:
            st.caption("📅 Unknown date")
    
    with col2:
        try:
            image_bytes = None
            if 'bytes' in img_data:
                image_bytes = img_data['bytes']
            elif 'bytes_b64' in img_data:
                image_bytes = base64.b64decode(img_data['bytes_b64'])
            
            if image_bytes:
                b64_img = base64.b64encode(image_bytes).decode()
                file_format = get_image_format_safe(img_data).lower()
                file_name = img_data.get('name', f'image_{index}')
                href = f'<a href="data:image/{file_format};base64,{b64_img}" download="{file_name}.{file_format}"><button style="width:100%; padding:6px; background:#4CAF50; color:white; border:none; border-radius:4px; cursor:pointer; font-size:12px; font-weight:bold;">⬇️ Download</button></a>'
                st.markdown(href, unsafe_allow_html=True)
        except Exception as e:
            st.button("⬇️ Download", disabled=True, use_container_width=True)
    
    st.divider()

def render_user_image_card(img_data, index):
    """Render individual image card for users - UPDATED FOR PAGINATION"""
    with st.container():
        # Display image at 50% width for better visibility
        col_image, col_info = st.columns([1.5, 1])  # 60% image, 40% info

        with col_image:
            try:
                # Check if we have bytes data in the expected format
                image_bytes = None
                if 'bytes' in img_data:
                    image_bytes = img_data['bytes']
                elif 'bytes_b64' in img_data:
                    image_bytes = base64.b64decode(img_data['bytes_b64'])
                
                if image_bytes:
                    st.image(
                        image_bytes,
                        use_container_width=True,
                        caption=img_data.get('name', 'Unnamed Image')
                    )
                else:
                    st.warning("📷 Image data not available")
            except Exception as e:
                st.error(f"❌ Error displaying image: {str(e)}")
                st.info("Image format may not be supported.")

        with col_info:
            # Image info on the right side
            st.markdown(f"**{img_data.get('name', 'Unnamed Image')}**")
            st.divider()

            # Description
            description = img_data.get('description', '')
            if description:
                preview = description[:100] + "..." if len(description) > 100 else description
                st.caption(f"📝 {preview}")
            else:
                st.caption("No description")

            # Strategy tags
            strategies = img_data.get('strategies', [])
            if strategies:
                st.caption(f"🏷️ **Strategies:**")
                for strategy in strategies[:3]:
                    st.caption(f"  • {strategy}")
                if len(strategies) > 3:
                    st.caption(f"  +{len(strategies) - 3} more")

            st.divider()

            # Metadata
            st.caption(f"👤 By: **{img_data.get('uploaded_by', 'Unknown')}**")
            timestamp = img_data.get('timestamp', '')
            if timestamp:
                try:
                    upload_time = datetime.fromisoformat(timestamp).strftime("%m/%d/%Y %H:%M")
                    st.caption(f"📅 {upload_time}")
                except:
                    st.caption(f"📅 {timestamp}")

            st.divider()

            # Interaction buttons - FULL WIDTH for better UX
            col_like, col_view = st.columns(2)

            with col_like:
                if st.button("❤️ Like", key=f"user_like_{index}_{img_data.get('id', index)}", use_container_width=True):
                    # Note: Like functionality would need to be implemented in the database
                    st.info("Like functionality requires database update implementation")
                    # img_data['likes'] = img_data.get('likes', 0) + 1
                    # save_gallery_images(st.session_state.uploaded_images)
                    # st.rerun()

            with col_view:
                if st.button("🖼️ Fullscreen", key=f"user_view_{index}_{img_data.get('id', index)}", use_container_width=True):
                    st.session_state.current_image_index = index
                    st.session_state.current_page_images = images  # Store current page images
                    st.session_state.image_viewer_mode = True
                    st.rerun()

            # Like count and download
            col_count, col_download = st.columns(2)
            with col_count:
                likes = img_data.get('likes', 0)
                st.metric("Likes", likes, label_visibility="collapsed")

            with col_download:
                try:
                    # Get image bytes for download
                    image_bytes = None
                    if 'bytes' in img_data:
                        image_bytes = img_data['bytes']
                    elif 'bytes_b64' in img_data:
                        image_bytes = base64.b64decode(img_data['bytes_b64'])
                    
                    if image_bytes:
                        b64_img = base64.b64encode(image_bytes).decode()
                        file_format = get_image_format_safe(img_data).lower()
                        file_name = img_data.get('name', f'image_{index}')
                        href = f'<a href="data:image/{file_format};base64,{b64_img}" download="{file_name}.{file_format}" style="text-decoration: none;">'
                        st.markdown(f'{href}<button style="background-color: #4CAF50; color: white; border: none; padding: 8px; text-align: center; text-decoration: none; display: inline-block; font-size: 12px; cursor: pointer; border-radius: 4px; width: 100%;">⬇️ Download</button></a>', unsafe_allow_html=True)
                    else:
                        st.caption("Download unavailable")
                except Exception as e:
                    st.caption("Download unavailable")

        st.markdown("---")

def render_image_viewer():
    """Image viewer for both admin and user galleries"""
    if not hasattr(st.session_state, 'current_page_images') or not st.session_state.current_page_images:
        st.warning("No images to display")
        st.session_state.image_viewer_mode = False
        st.rerun()
        return

    current_images = st.session_state.current_page_images
    current_index = st.session_state.current_image_index
    
    if current_index >= len(current_images):
        st.session_state.current_image_index = 0
        current_index = 0

    img_data = current_images[current_index]

    # Header with navigation
    col1, col2, col3, col4, col5 = st.columns([1, 1, 2, 1, 1])
    
    with col1:
        if st.button("⬅️ Back", use_container_width=True, key="viewer_back"):
            st.session_state.image_viewer_mode = False
            st.rerun()
            
    with col2:
        if st.button("◀️ Previous", use_container_width=True, disabled=current_index == 0, key="viewer_prev"):
            st.session_state.current_image_index = max(0, current_index - 1)
            st.rerun()
            
    with col3:
        st.markdown(f"### {img_data.get('name', 'Image Viewer')}")
        st.caption(f"Image {current_index + 1} of {len(current_images)}")
        
    with col4:
        if st.button("Next ▶️", use_container_width=True, disabled=current_index >= len(current_images) - 1, key="viewer_next"):
            st.session_state.current_image_index = min(len(current_images) - 1, current_index + 1)
            st.rerun()
            
    with col5:
        if st.button("📋 Close", use_container_width=True, key="viewer_close"):
            st.session_state.image_viewer_mode = False
            st.rerun()

    st.markdown("---")

    # Display the image at full width
    try:
        # Get image bytes
        image_bytes = None
        if 'bytes' in img_data:
            image_bytes = img_data['bytes']
        elif 'bytes_b64' in img_data:
            image_bytes = base64.b64decode(img_data['bytes_b64'])
        
        if image_bytes:
            st.image(image_bytes, use_container_width=True, caption=img_data.get('name', ''))
        else:
            st.error("❌ Unable to load image data")
    except Exception as e:
        st.error(f"❌ Error displaying image: {str(e)}")

    # Image details
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Image Details")
        st.write(f"**Name:** {img_data.get('name', 'N/A')}")
        st.write(f"**Uploaded by:** {img_data.get('uploaded_by', 'N/A')}")
        st.write(f"**Format:** {img_data.get('format', 'N/A')}")
        
        timestamp = img_data.get('timestamp', '')
        if timestamp:
            try:
                upload_time = datetime.fromisoformat(timestamp).strftime("%Y-%m-%d %H:%M:%S")
                st.write(f"**Uploaded:** {upload_time}")
            except:
                st.write(f"**Uploaded:** {timestamp}")
                
        st.write(f"**Likes:** {img_data.get('likes', 0)}")

    with col2:
        st.subheader("Description & Strategies")
        description = img_data.get('description', '')
        if description:
            st.write(description)
        else:
            st.info("No description provided")
            
        strategies = img_data.get('strategies', [])
        if strategies:
            st.write("**Related Strategies:**")
            for strategy in strategies:
                st.write(f"• {strategy}")
        else:
            st.info("No strategies tagged")

    # Download button
    st.markdown("---")
    try:
        image_bytes = None
        if 'bytes' in img_data:
            image_bytes = img_data['bytes']
        elif 'bytes_b64' in img_data:
            image_bytes = base64.b64decode(img_data['bytes_b64'])
            
        if image_bytes:
            b64_img = base64.b64encode(image_bytes).decode()
            file_format = get_image_format_safe(img_data).lower()
            file_name = img_data.get('name', f'image_{current_index}')
            href = f'<a href="data:image/{file_format};base64,{b64_img}" download="{file_name}.{file_format}" style="text-decoration: none;">'
            st.markdown(f'{href}<button style="background-color: #4CAF50; color: white; border: none; padding: 12px 24px; text-align: center; text-decoration: none; display: inline-block; font-size: 16px; margin: 4px 2px; cursor: pointer; border-radius: 4px; width: 100%;">⬇️ Download Full Resolution Image</button></a>', unsafe_allow_html=True)
    except Exception as e:
        st.error("Download unavailable")

